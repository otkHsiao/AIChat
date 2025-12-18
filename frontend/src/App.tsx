import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { FluentProvider } from '@fluentui/react-components'
import { Provider } from 'react-redux'

import { store, useAppSelector } from './store'
import { lightTheme, darkTheme } from './theme'
import AppLayout from './components/Layout/AppLayout'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import ChatPage from './pages/ChatPage'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ToastProvider } from './components/Toast'
import { OfflineIndicator } from './components/OfflineIndicator'
import { PWAUpdatePrompt } from './components/PWAUpdatePrompt'
import { PWAInstallPrompt } from './components/PWAInstallPrompt'

// Auth guard component
function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useAppSelector((state) => state.auth.token)

  if (!token) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

// Theme provider that reads from Redux state
function ThemedApp() {
  const theme = useAppSelector((state) => state.ui.theme)
  const currentTheme = theme === 'dark' ? darkTheme : lightTheme

  return (
    <FluentProvider theme={currentTheme}>
      <ToastProvider>
        <OfflineIndicator />
        <PWAUpdatePrompt />
        <PWAInstallPrompt />
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route
              path="/"
              element={
                <RequireAuth>
                  <AppLayout />
                </RequireAuth>
              }
            >
              <Route index element={<ChatPage />} />
              <Route path="chat" element={<ChatPage />} />
              <Route path="chat/:conversationId" element={<ChatPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </FluentProvider>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <Provider store={store}>
        <ThemedApp />
      </Provider>
    </ErrorBoundary>
  )
}