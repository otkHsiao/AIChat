import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { User } from '../../types'

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

// Check for existing token in localStorage
const storedToken = localStorage.getItem('accessToken')
const storedRefreshToken = localStorage.getItem('refreshToken')
const storedUser = localStorage.getItem('user')

const initialState: AuthState = {
  user: storedUser ? JSON.parse(storedUser) : null,
  token: storedToken,
  refreshToken: storedRefreshToken,
  isAuthenticated: !!storedToken,
  isLoading: false,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (
      state,
      action: PayloadAction<{
        user: User
        accessToken: string
        refreshToken: string
      }>
    ) => {
      const { user, accessToken, refreshToken } = action.payload
      state.user = user
      state.token = accessToken
      state.refreshToken = refreshToken
      state.isAuthenticated = true
      state.isLoading = false

      // Persist to localStorage
      localStorage.setItem('accessToken', accessToken)
      localStorage.setItem('refreshToken', refreshToken)
      localStorage.setItem('user', JSON.stringify(user))
    },

    updateToken: (state, action: PayloadAction<string>) => {
      state.token = action.payload
      localStorage.setItem('accessToken', action.payload)
    },

    updateUser: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload }
        localStorage.setItem('user', JSON.stringify(state.user))
      }
    },

    logout: (state) => {
      state.user = null
      state.token = null
      state.refreshToken = null
      state.isAuthenticated = false
      state.isLoading = false

      // Clear localStorage
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
      localStorage.removeItem('user')
    },

    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
  },
})

export const { setCredentials, updateToken, updateUser, logout, setLoading } =
  authSlice.actions

export default authSlice.reducer