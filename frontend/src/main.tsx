import React from 'react'
import ReactDOM from 'react-dom/client'
import { registerSW } from 'virtual:pwa-register'
import App from './App'
import './index.css'

// Register PWA Service Worker with auto update
const updateSW = registerSW({
  onNeedRefresh() {
    // New content is available, show update notification
    console.log('New content available, please refresh.')
    window.dispatchEvent(new CustomEvent('sw-update-available'))
  },
  onOfflineReady() {
    console.log('App ready to work offline')
  },
  onRegistered(registration) {
    console.log('PWA Service Worker registered:', registration?.scope)
    
    // Check for updates periodically (every hour)
    if (registration) {
      setInterval(() => {
        registration.update()
      }, 60 * 60 * 1000)
    }
  },
  onRegisterError(error) {
    console.error('PWA Service Worker registration failed:', error)
  }
})

// Export for manual update trigger
export { updateSW }

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)