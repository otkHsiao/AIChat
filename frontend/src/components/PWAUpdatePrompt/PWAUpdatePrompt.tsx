import React, { useEffect, useState } from 'react'
import {
  Button,
  Card,
  CardFooter,
  Text,
  makeStyles,
  tokens,
} from '@fluentui/react-components'
import { ArrowSync24Regular } from '@fluentui/react-icons'

const useStyles = makeStyles({
  container: {
    position: 'fixed',
    bottom: '20px',
    left: '50%',
    transform: 'translateX(-50%)',
    zIndex: 9999,
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
  footer: {
    justifyContent: 'flex-end',
    gap: '8px',
  },
})

export const PWAUpdatePrompt: React.FC = () => {
  const styles = useStyles()
  const [showPrompt, setShowPrompt] = useState(false)

  useEffect(() => {
    const handleUpdate = () => {
      setShowPrompt(true)
    }

    window.addEventListener('sw-update-available', handleUpdate)

    return () => {
      window.removeEventListener('sw-update-available', handleUpdate)
    }
  }, [])

  const handleRefresh = () => {
    window.location.reload()
  }

  const handleDismiss = () => {
    setShowPrompt(false)
  }

  if (!showPrompt) {
    return null
  }

  return (
    <Card className={styles.container}>
      <div className={styles.content}>
        <ArrowSync24Regular className={styles.icon} />
        <Text className={styles.text}>
          发现新版本！刷新页面以获取最新功能。
        </Text>
      </div>
      <CardFooter className={styles.footer}>
        <Button appearance="subtle" onClick={handleDismiss}>
          稍后
        </Button>
        <Button appearance="primary" onClick={handleRefresh}>
          立即刷新
        </Button>
      </CardFooter>
    </Card>
  )
}

export default PWAUpdatePrompt