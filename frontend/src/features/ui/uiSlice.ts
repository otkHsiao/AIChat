import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface UiState {
  sidebarOpen: boolean
  theme: 'light' | 'dark'
  settingsOpen: boolean
}

// Get theme from localStorage or system preference
const getInitialTheme = (): 'light' | 'dark' => {
  const stored = localStorage.getItem('theme')
  if (stored === 'light' || stored === 'dark') {
    return stored
  }
  // Check system preference
  if (window.matchMedia?.('(prefers-color-scheme: dark)').matches) {
    return 'dark'
  }
  return 'light'
}

const initialState: UiState = {
  sidebarOpen: true,
  theme: getInitialTheme(),
  settingsOpen: false,
}

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen
    },

    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload
    },

    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload
      localStorage.setItem('theme', action.payload)
    },

    toggleTheme: (state) => {
      const newTheme = state.theme === 'light' ? 'dark' : 'light'
      state.theme = newTheme
      localStorage.setItem('theme', newTheme)
    },

    setSettingsOpen: (state, action: PayloadAction<boolean>) => {
      state.settingsOpen = action.payload
    },

    toggleSettings: (state) => {
      state.settingsOpen = !state.settingsOpen
    },
  },
})

export const {
  toggleSidebar,
  setSidebarOpen,
  setTheme,
  toggleTheme,
  setSettingsOpen,
  toggleSettings,
} = uiSlice.actions

export default uiSlice.reducer