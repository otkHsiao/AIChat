import {
  makeStyles,
  tokens,
  Text,
  Menu,
  MenuTrigger,
  MenuPopover,
  MenuList,
  MenuItem,
  Button,
} from '@fluentui/react-components'
import {
  ChatRegular,
  MoreHorizontalRegular,
  EditRegular,
  DeleteRegular,
} from '@fluentui/react-icons'

import type { Conversation } from '../../types'

const useStyles = makeStyles({
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalXS,
  },
  item: {
    display: 'flex',
    alignItems: 'center',
    padding: `${tokens.spacingVerticalS} ${tokens.spacingHorizontalM}`,
    borderRadius: tokens.borderRadiusMedium,
    cursor: 'pointer',
    transition: 'background-color 0.1s',
    ':hover': {
      backgroundColor: tokens.colorNeutralBackground1Hover,
    },
  },
  itemActive: {
    backgroundColor: tokens.colorNeutralBackground1Selected,
    ':hover': {
      backgroundColor: tokens.colorNeutralBackground1Selected,
    },
  },
  icon: {
    marginRight: tokens.spacingHorizontalS,
    color: tokens.colorNeutralForeground2,
  },
  title: {
    flex: 1,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  menuButton: {
    opacity: 0,
    transition: 'opacity 0.1s',
  },
  itemHover: {
    ':hover .menu-button': {
      opacity: 1,
    },
  },
  empty: {
    padding: tokens.spacingVerticalXXL,
    textAlign: 'center',
    color: tokens.colorNeutralForeground3,
  },
})

interface ConversationListProps {
  conversations: Conversation[]
  currentId: string | null
  onSelect: (id: string) => void
  onDelete?: (id: string) => void
  onRename?: (id: string, title: string) => void
}

export default function ConversationList({
  conversations,
  currentId,
  onSelect,
  onDelete,
  onRename,
}: ConversationListProps) {
  const classes = useStyles()

  if (conversations.length === 0) {
    return (
      <div className={classes.empty}>
        <Text>暂无对话</Text>
        <br />
        <Text size={200}>点击"新建对话"开始聊天</Text>
      </div>
    )
  }

  return (
    <div className={classes.list}>
      {conversations.map((conversation) => (
        <div
          key={conversation.id}
          className={`${classes.item} ${
            conversation.id === currentId ? classes.itemActive : ''
          }`}
          onClick={() => onSelect(conversation.id)}
        >
          <ChatRegular className={classes.icon} />
          <Text className={classes.title}>{conversation.title}</Text>

          <Menu>
            <MenuTrigger disableButtonEnhancement>
              <Button
                appearance="subtle"
                size="small"
                icon={<MoreHorizontalRegular />}
                onClick={(e) => e.stopPropagation()}
                aria-label="更多操作"
              />
            </MenuTrigger>
            <MenuPopover>
              <MenuList>
                <MenuItem
                  icon={<EditRegular />}
                  onClick={(e) => {
                    e.stopPropagation()
                    // TODO: Implement rename
                    onRename?.(conversation.id, conversation.title)
                  }}
                >
                  重命名
                </MenuItem>
                <MenuItem
                  icon={<DeleteRegular />}
                  onClick={(e) => {
                    e.stopPropagation()
                    onDelete?.(conversation.id)
                  }}
                >
                  删除
                </MenuItem>
              </MenuList>
            </MenuPopover>
          </Menu>
        </div>
      ))}
    </div>
  )
}