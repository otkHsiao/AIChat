import { makeStyles, tokens, Skeleton, SkeletonItem } from '@fluentui/react-components'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    padding: tokens.spacingHorizontalM,
    gap: tokens.spacingVerticalS,
  },
  header: {
    marginBottom: tokens.spacingVerticalM,
  },
  item: {
    display: 'flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalS,
    padding: tokens.spacingVerticalS,
  },
})

export function SidebarSkeleton() {
  const classes = useStyles()

  return (
    <div className={classes.container}>
      <Skeleton>
        {/* New chat button skeleton */}
        <div className={classes.header}>
          <SkeletonItem size={36} style={{ width: '100%' }} />
        </div>

        {/* Conversation items skeleton */}
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className={classes.item}>
            <SkeletonItem shape="circle" size={24} />
            <SkeletonItem size={16} style={{ flex: 1 }} />
          </div>
        ))}
      </Skeleton>
    </div>
  )
}

export default SidebarSkeleton