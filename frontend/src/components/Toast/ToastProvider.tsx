import { createContext, useContext, useCallback, ReactNode } from 'react'
import {
  Toaster,
  useToastController,
  Toast,
  ToastTitle,
  ToastBody,
  ToastIntent,
  useId,
} from '@fluentui/react-components'

interface ToastOptions {
  title: string
  body?: string
  intent?: ToastIntent
  timeout?: number
}

interface ToastContextValue {
  showToast: (options: ToastOptions) => void
  showSuccess: (title: string, body?: string) => void
  showError: (title: string, body?: string) => void
  showWarning: (title: string, body?: string) => void
  showInfo: (title: string, body?: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

interface ToastProviderProps {
  children: ReactNode
}

function ToastProviderInner({ children }: ToastProviderProps) {
  const toasterId = useId('toaster')
  const { dispatchToast } = useToastController(toasterId)

  const showToast = useCallback(
    ({ title, body, intent = 'info', timeout = 3000 }: ToastOptions) => {
      dispatchToast(
        <Toast>
          <ToastTitle>{title}</ToastTitle>
          {body && <ToastBody>{body}</ToastBody>}
        </Toast>,
        { intent, timeout }
      )
    },
    [dispatchToast]
  )

  const showSuccess = useCallback(
    (title: string, body?: string) => {
      showToast({ title, body, intent: 'success' })
    },
    [showToast]
  )

  const showError = useCallback(
    (title: string, body?: string) => {
      showToast({ title, body, intent: 'error', timeout: 5000 })
    },
    [showToast]
  )

  const showWarning = useCallback(
    (title: string, body?: string) => {
      showToast({ title, body, intent: 'warning', timeout: 4000 })
    },
    [showToast]
  )

  const showInfo = useCallback(
    (title: string, body?: string) => {
      showToast({ title, body, intent: 'info' })
    },
    [showToast]
  )

  return (
    <ToastContext.Provider
      value={{ showToast, showSuccess, showError, showWarning, showInfo }}
    >
      {children}
      <Toaster toasterId={toasterId} position="top-end" />
    </ToastContext.Provider>
  )
}

// 包装组件，确保 Toaster 在 FluentProvider 内部
export function ToastProvider({ children }: ToastProviderProps) {
  return <ToastProviderInner>{children}</ToastProviderInner>
}

export default ToastProvider