import type { RootState } from '../../store'

export const selectUser = (state: RootState) => state.auth.user
export const selectToken = (state: RootState) => state.auth.token
export const selectIsAuthenticated = (state: RootState) => state.auth.isAuthenticated
export const selectIsAuthLoading = (state: RootState) => state.auth.isLoading