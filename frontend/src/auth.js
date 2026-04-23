import { useDispatch, useSelector } from 'react-redux'
import { forceLogout, loginThunk, logoutThunk, refreshUserThunk, selectAuthState, signupThunk } from './store/slices/authSlice'

export function useAuth() {
  const dispatch = useDispatch()
  const auth = useSelector(selectAuthState)

  return {
    user: auth.user,
    token: auth.token,
    sessionId: auth.sessionId,
    expiresAt: auth.expiresAt,
    isAuthenticated: Boolean(auth.token),
    isLoading: auth.status === 'loading',
    error: auth.error,
    login: (payload) => dispatch(loginThunk(payload)).unwrap(),
    signup: (payload) => dispatch(signupThunk(payload)).unwrap(),
    logout: () => dispatch(logoutThunk()).unwrap(),
    refreshUser: () => dispatch(refreshUserThunk()).unwrap(),
    forceLogout: () => dispatch(forceLogout()),
  }
}
