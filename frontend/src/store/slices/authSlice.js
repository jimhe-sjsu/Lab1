import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import {
  clearPersistedAuthState,
  fetchCurrentUserForRole,
  fetchReviewerDashboard,
  loadPersistedAuthState,
  loginOwner,
  loginReviewer,
  logoutForRole,
  persistAuthState,
  signupOwner,
  signupReviewer,
} from '../../api'

function buildSessionState({ tokenData, profile, role, dashboard }) {
  return {
    token: tokenData.access_token,
    sessionId: tokenData.session_id,
    expiresAt: tokenData.expires_at,
    user: {
      fullName: profile?.name || profile?.email?.split('@')?.[0] || 'User',
      email: profile?.email || '',
      role,
      userId: profile?.id || null,
      totalReviews: dashboard?.total_reviews ?? 0,
      totalFavorites: dashboard?.total_favorites ?? 0,
    },
    status: 'succeeded',
    error: null,
  }
}

const persisted = loadPersistedAuthState()

const initialState = persisted
  ? {
      ...persisted,
      status: 'idle',
      error: null,
    }
  : {
      token: null,
      sessionId: null,
      expiresAt: null,
      user: null,
      status: 'idle',
      error: null,
    }

export const loginThunk = createAsyncThunk('auth/login', async ({ email, password, role }) => {
  const tokenData = role === 'OWNER' ? await loginOwner({ email, password }) : await loginReviewer({ email, password })
  const profile = await fetchCurrentUserForRole(role, tokenData.access_token)
  let dashboard = null
  if (role !== 'OWNER') {
    try {
      dashboard = await fetchReviewerDashboard(tokenData.access_token)
    } catch {
      dashboard = null
    }
  }
  const sessionState = buildSessionState({ tokenData, profile, role, dashboard })
  persistAuthState(sessionState)
  return sessionState
})

export const signupThunk = createAsyncThunk('auth/signup', async ({ fullName, email, password, role, restaurantLocation }, thunkAPI) => {
  if (role === 'OWNER') {
    await signupOwner({ fullName, email, password, restaurantLocation })
  } else {
    await signupReviewer({ fullName, email, password })
  }
  return thunkAPI.dispatch(loginThunk({ email, password, role })).unwrap()
})

export const refreshUserThunk = createAsyncThunk('auth/refreshUser', async (_, thunkAPI) => {
  const state = thunkAPI.getState().auth
  if (!state?.token || !state?.user?.role) {
    throw new Error('Not authenticated')
  }
  const role = state.user.role
  const tokenData = {
    access_token: state.token,
    session_id: state.sessionId,
    expires_at: state.expiresAt,
  }
  const profile = await fetchCurrentUserForRole(role, state.token)
  let dashboard = null
  if (role !== 'OWNER') {
    try {
      dashboard = await fetchReviewerDashboard(state.token)
    } catch {
      dashboard = null
    }
  }
  const sessionState = buildSessionState({ tokenData, profile, role, dashboard })
  persistAuthState(sessionState)
  return sessionState
})

export const logoutThunk = createAsyncThunk('auth/logout', async (_, thunkAPI) => {
  const state = thunkAPI.getState().auth
  try {
    if (state?.token && state?.user?.role) {
      await logoutForRole(state.user.role, state.token)
    }
  } finally {
    clearPersistedAuthState()
  }
})

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    forceLogout(state) {
      clearPersistedAuthState()
      state.token = null
      state.sessionId = null
      state.expiresAt = null
      state.user = null
      state.status = 'idle'
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loginThunk.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(loginThunk.fulfilled, (state, action) => {
        state.token = action.payload.token
        state.sessionId = action.payload.sessionId
        state.expiresAt = action.payload.expiresAt
        state.user = action.payload.user
        state.status = 'succeeded'
        state.error = null
      })
      .addCase(loginThunk.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message || 'Login failed.'
      })
      .addCase(signupThunk.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(signupThunk.fulfilled, (state, action) => {
        state.token = action.payload.token
        state.sessionId = action.payload.sessionId
        state.expiresAt = action.payload.expiresAt
        state.user = action.payload.user
        state.status = 'succeeded'
        state.error = null
      })
      .addCase(signupThunk.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message || 'Signup failed.'
      })
      .addCase(refreshUserThunk.fulfilled, (state, action) => {
        state.token = action.payload.token
        state.sessionId = action.payload.sessionId
        state.expiresAt = action.payload.expiresAt
        state.user = action.payload.user
        state.status = 'succeeded'
        state.error = null
      })
      .addCase(refreshUserThunk.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message || 'Could not refresh user.'
      })
      .addCase(logoutThunk.fulfilled, (state) => {
        state.token = null
        state.sessionId = null
        state.expiresAt = null
        state.user = null
        state.status = 'idle'
        state.error = null
      })
  },
})

export const { forceLogout } = authSlice.actions
export const selectAuthState = (state) => state.auth

export default authSlice.reducer
