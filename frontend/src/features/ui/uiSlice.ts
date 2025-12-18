import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface UiState {
  sidebarOpen: boolean
  theme: 'light' | 'dark'
  settingsOpen: boolean
  isMobileView: boolean
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

// Check if initial view is mobile
const getInitialMobileView = (): boolean => {
  if (typeof window !== 'undefined') {
    return window.innerWidth <= 768
  }
  return false
}

const initialState: UiState = {
  // 移动端默认关闭侧边栏，桌面端默认打开
  sidebarOpen: !getInitialMobileView(),
  theme: getInitialTheme(),
  settingsOpen: false,
  isMobileView: getInitialMobileView(),
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

    setMobileView: (state, action: PayloadAction<boolean>) => {
      state.isMobileView = action.payload
      // 切换到移动视图时自动关闭侧边栏
      if (action.payload && state.sidebarOpen) {
        state.sidebarOpen = false
      }
    },

    // 移动端选择对话后自动关闭侧边栏
    closeSidebarOnMobile: (state) => {
      if (state.isMobileView) {
        state.sidebarOpen = false
      }
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
  setMobileView,
  closeSidebarOnMobile,
} = uiSlice.actions

export default uiSlice.reducer