import React, { useEffect, useState } from 'react'
import {
  Button,
  Card,
  CardFooter,
  Text,
  makeStyles,
  tokens,
} from '@fluentui/react-components'
import { AppGeneric24Regular, Dismiss24Regular } from '@fluentui/react-icons'

const useStyles = makeStyles({
  container: {
    position: 'fixed',
    bottom: '20px',
    left: '50%',
    transform: 'translateX(-50%)',
    zIndex: 9998,
    boxShadow: tokens.shadow16,
    maxWidth: '400px',
    width: 'calc(100% - 40px)',
  },
  content: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '16px',
  },
  icon: {
    flexShrink: 0,
    color: tokens.colorBrandForeground1,
  },
  text: {
    flex: 1,
  },
  title: {
    fontWeight: tokens.fontWeightSemibold,
    marginBottom: '4px',
  },
  description: {
    color: tokens.colorNeutralForeground2,
    fontSize: tokens.fontSizeBase200,
  },
  footer: {
    justifyContent: 'flex-end',
    gap: '8px',
  },
  closeButton: {
    position: 'absolute',
    top: '8px',
    right: '8px',
    minWidth: 'auto',
    padding: '4px',
  },
})

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

export const PWAInstallPrompt: React.FC = () => {
  const styles = useStyles()
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [showPrompt, setShowPrompt] = useState(false)

  useEffect(() => {
    // Check if already installed
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches
    if (isStandalone) {
      return
    }

    // Check if user dismissed the prompt before
    const dismissed = localStorage.getItem('pwa-install-dismissed')
    if (dismissed) {
      const dismissedTime = parseInt(dismissed, 10)
      // Show again after 7 days
      if (Date.now() - dismissedTime < 7 * 24 * 60 * 60 * 1000) {
        return
      }
    }

    const handleBeforeInstall = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e as BeforeInstallPromptEvent)
      // Delay showing the prompt for better UX
      setTimeout(() => setShowPrompt(true), 3000)
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstall)

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall)
    }
  }, [])

  const handleInstall = async () => {
    if (!deferredPrompt) return

    try {
      await deferredPrompt.prompt()
      const { outcome } = await deferredPrompt.userChoice
      
      if (outcome === 'accepted') {
        console.log('PWA installed')
      }
      
      setDeferredPrompt(null)
      setShowPrompt(false)
    } catch (error) {
      console.error('PWA install error:', error)
    }
  }

  const handleDismiss = () => {
    localStorage.setItem('pwa-install-dismissed', Date.now().toString())
    setShowPrompt(false)
  }

  if (!showPrompt || !deferredPrompt) {
    return null
  }

  return (
    <Card className={styles.container}>
      <Button
        appearance="subtle"
        className={styles.closeButton}
        icon={<Dismiss24Regular />}
        onClick={handleDismiss}
        aria-label="关闭"
      />
      <div className={styles.content}>
        <AppGeneric24Regular className={styles.icon} />
        <div className={styles.text}>
          <Text className={styles.title} block>
            安装 AI Chat
          </Text>
          <Text className={styles.description} block>
            将应用添加到主屏幕，获得更好的体验
          </Text>
        </div>
      </div>
      <CardFooter className={styles.footer}>
        <Button appearance="subtle" onClick={handleDismiss}>
          以后再说
        </Button>
        <Button appearance="primary" onClick={handleInstall}>
          安装
        </Button>
      </CardFooter>
    </Card>
  )
}

export default PWAInstallPrompt