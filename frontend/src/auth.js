import { createContext, createElement, useContext, useEffect, useState } from 'react'
import api, { TOKEN_KEY } from './api'

const AUTH_STATE_KEY = 'lab1_auth_state'
const AuthContext = createContext(null)

const mockUserFromEmail = (email) => {
  const localPart = email.split('@')[0] || 'Student'
  return {
    fullName: localPart.charAt(0).toUpperCase() + localPart.slice(1),
    email,
    city: 'San Jose',
    favoriteCuisines: ['Japanese', 'Mexican'],
    dietaryPreferences: ['Vegetarian options'],
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

  const useMockAuth = import.meta.env.VITE_USE_MOCK_AUTH !== 'false'

  const login = async ({ email, password }) => {
    if (!email || !password) {
      throw new Error('Email and password are required.')
    }

    setIsLoading(true)
    try {
      if (useMockAuth) {
        const token = `mock-token-${Date.now()}`
        setAuthState({ token, user: mockUserFromEmail(email) })
        return
      }

      const { data } = await api.post('/auth/login', { email, password })
      setAuthState({ token: data.token, user: data.user })
    } finally {
      setIsLoading(false)
    }
  }

  const signup = async ({ fullName, email, password }) => {
    if (!fullName || !email || !password) {
      throw new Error('Name, email, and password are required.')
    }

    setIsLoading(true)
    try {
      if (useMockAuth) {
        const token = `mock-token-${Date.now()}`
        setAuthState({
          token,
          user: { ...mockUserFromEmail(email), fullName },
        })
        return
      }

      const { data } = await api.post('/auth/signup', { fullName, email, password })
      setAuthState({ token: data.token, user: data.user })
    } finally {
      setIsLoading(false)
    }
  }

  const updateProfile = async (profileUpdates) => {
    setIsLoading(true)
    try {
      if (useMockAuth) {
        setAuthState((prev) => ({
          ...prev,
          user: {
            ...prev.user,
            ...profileUpdates,
          },
        }))
        return
      }

      const { data } = await api.put('/users/me', profileUpdates)
      setAuthState((prev) => ({ ...prev, user: data.user }))
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
    updateProfile,
    logout,
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
