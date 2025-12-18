import { makeStyles, tokens, Skeleton, SkeletonItem } from '@fluentui/react-components'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    padding: tokens.spacingHorizontalL,
    gap: tokens.spacingVerticalL,
  },
  messageRow: {
    display: 'flex',
    gap: tokens.spacingHorizontalM,
    alignItems: 'flex-start',
  },
  messageRowReverse: {
    display: 'flex',
    gap: tokens.spacingHorizontalM,
    alignItems: 'flex-start',
    flexDirection: 'row-reverse',
  },
  avatar: {
    flexShrink: 0,
  },
  messageContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalXS,
    flex: 1,
    maxWidth: '70%',
  },
})

export function ChatSkeleton() {
  const classes = useStyles()

  return (
    <div className={classes.container}>
      <Skeleton>
        {/* User message */}
        <div className={classes.messageRowReverse}>
          <SkeletonItem
            className={classes.avatar}
            shape="circle"
            size={32}
          />
          <div className={classes.messageContent}>
            <SkeletonItem size={16} style={{ width: '60%' }} />
            <SkeletonItem size={16} style={{ width: '80%' }} />
          </div>
        </div>

        {/* Assistant message */}
        <div className={classes.messageRow}>
          <SkeletonItem
            className={classes.avatar}
            shape="circle"
            size={32}
          />
          <div className={classes.messageContent}>
            <SkeletonItem size={16} style={{ width: '90%' }} />
            <SkeletonItem size={16} style={{ width: '70%' }} />
            <SkeletonItem size={16} style={{ width: '85%' }} />
          </div>
        </div>

        {/* User message */}
        <div className={classes.messageRowReverse}>
          <SkeletonItem
            className={classes.avatar}
            shape="circle"
            size={32}
          />
          <div className={classes.messageContent}>
            <SkeletonItem size={16} style={{ width: '50%' }} />
          </div>
        </div>

        {/* Assistant message */}
        <div className={classes.messageRow}>
          <SkeletonItem
            className={classes.avatar}
            shape="circle"
            size={32}
          />
          <div className={classes.messageContent}>
            <SkeletonItem size={16} style={{ width: '75%' }} />
            <SkeletonItem size={16} style={{ width: '60%' }} />
          </div>
        </div>
      </Skeleton>
    </div>
  )
}

export default ChatSkeleton