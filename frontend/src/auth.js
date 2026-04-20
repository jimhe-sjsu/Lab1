import { createContext, createElement, useContext, useEffect, useState } from 'react'
import api, { TOKEN_KEY, fetchCurrentUser, fetchDashboardSummary } from './api'

const AUTH_STATE_KEY = 'lab1_auth_state'
const AuthContext = createContext(null)

function decodeToken(token) {
  try {
    const payload = token.split('.')[1]
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/')
    const decoded = JSON.parse(window.atob(normalized))
    return {
      userId: decoded.sub ? Number(decoded.sub) : null,
      role: decoded.role || 'USER',
    }
  } catch {
    return { userId: null, role: 'USER' }
  }
}

export function AuthProvider({ children }) {
  const [authState, setAuthState] = useState(() => {
    const cached = localStorage.getItem(AUTH_STATE_KEY)
    return cached ? JSON.parse(cached) : { token: null, user: null }
  })
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    localStorage.setItem(AUTH_STATE_KEY, JSON.stringify(authState))
    if (authState.token) {
      localStorage.setItem(TOKEN_KEY, authState.token)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }, [authState])

  useEffect(() => {
    const handleUnauthorized = () => setAuthState({ token: null, user: null })
    window.addEventListener('auth:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized)
  }, [])

  const refreshUser = async (token, fallbackEmail) => {
    const tokenData = decodeToken(token)

    let profile = null
    let dashboard = null

    try {
      profile = await fetchCurrentUser()
    } catch {
      profile = null
    }

    try {
      dashboard = await fetchDashboardSummary()
    } catch {
      dashboard = null
    }

    const fallbackName = fallbackEmail ? fallbackEmail.split('@')[0] : 'User'

    setAuthState({
      token,
      user: {
        fullName: profile?.name || fallbackName,
        email: profile?.email || dashboard?.user || fallbackEmail || '',
        role: profile?.role || tokenData.role,
        userId: tokenData.userId,
        totalReviews: dashboard?.total_reviews ?? 0,
        totalFavorites: dashboard?.total_favorites ?? 0,
      },
    })
  }

  const login = async ({ email, password }) => {
    if (!email || !password) {
      throw new Error('Email and password are required.')
    }

    setIsLoading(true)
    try {
      const payload = new URLSearchParams()
      payload.set('username', email)
      payload.set('password', password)

      const { data } = await api.post('/auth/login', payload, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })

      await refreshUser(data.access_token, email)
    } catch (error) {
      const message = error?.response?.data?.detail || 'Login failed. Please try again.'
      throw new Error(message)
    } finally {
      setIsLoading(false)
    }
  }

  const signup = async ({ fullName, email, password, role = 'USER', restaurantLocation = '' }) => {
    if (!fullName || !email || !password) {
      throw new Error('Name, email, and password are required.')
    }

    if (role === 'OWNER' && !restaurantLocation.trim()) {
      throw new Error('Restaurant location is required for owner signup.')
    }

    setIsLoading(true)
    try {
      await api.post('/auth/signup', {
        name: fullName,
        email,
        password,
        role,
        restaurant_location: role === 'OWNER' ? restaurantLocation.trim() : null,
      })

      await login({ email, password })
    } catch (error) {
      const detail = error?.response?.data?.detail
      const message = Array.isArray(detail) ? detail[0]?.msg : detail || 'Signup failed. Please try again.'
      throw new Error(message)
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    setAuthState({ token: null, user: null })
  }

  const value = {
    user: authState.user,
    token: authState.token,
    isAuthenticated: Boolean(authState.token),
    isLoading,
    login,
    signup,
    logout,
    refreshUser,
  }

  return createElement(AuthContext.Provider, { value }, children)
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return context
}
