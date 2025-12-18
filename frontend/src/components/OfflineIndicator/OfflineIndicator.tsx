import { makeStyles, tokens, MessageBar, MessageBarBody } from '@fluentui/react-components'
import { WifiOff24Regular } from '@fluentui/react-icons'
import { useOnlineStatus } from '../../hooks/useOnlineStatus'

const useStyles = makeStyles({
  container: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 9999,
    display: 'flex',
    justifyContent: 'center',
    padding: tokens.spacingVerticalS,
    backgroundColor: tokens.colorPaletteYellowBackground2,
    borderBottom: `1px solid ${tokens.colorPaletteYellowBorder2}`,
    animation: 'slideDown 0.3s ease-out',
    '@keyframes slideDown': {
      from: {
        transform: 'translateY(-100%)',
        opacity: 0,
      },
      to: {
        transform: 'translateY(0)',
        opacity: 1,
      },
    },
  },
  messageBar: {
    maxWidth: '600px',
    width: '100%',
  },
  icon: {
    marginRight: tokens.spacingHorizontalS,
    color: tokens.colorPaletteYellowForeground2,
  },
})

export function OfflineIndicator() {
  const classes = useStyles()
  const isOnline = useOnlineStatus()

  if (isOnline) {
    return null
  }

  return (
    <div className={classes.container}>
      <MessageBar intent="warning" className={classes.messageBar}>
        <MessageBarBody>
          <WifiOff24Regular className={classes.icon} />
          网络连接已断开，部分功能可能无法使用
        </MessageBarBody>
      </MessageBar>
    </div>
  )
}

export default OfflineIndicator