import { useNavigate } from 'react-router-dom'
import {
  ToolbarButton,
  ToolbarDivider,
  Menu,
  MenuTrigger,
  MenuPopover,
  MenuList,
  MenuItem,
  Avatar,
  makeStyles,
  tokens,
  Tooltip,
} from '@fluentui/react-components'
import {
  NavigationRegular,
  WeatherMoonRegular,
  WeatherSunnyRegular,
  SettingsRegular,
  SignOutRegular,
  PersonRegular,
  AddRegular,
} from '@fluentui/react-icons'

import { useAppDispatch, useAppSelector } from '../../hooks/useAppDispatch'
import { toggleSidebar, toggleTheme } from '../../features/ui/uiSlice'
import { logout } from '../../features/auth/authSlice'
import { selectUser } from '../../features/auth/authSelectors'
import { createConversation } from '../../features/conversations/conversationsSlice'
import { useToast } from '../Toast'

const useStyles = makeStyles({
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: `${tokens.spacingVerticalS} ${tokens.spacingHorizontalM}`,
    borderBottom: `1px solid ${tokens.colorNeutralStroke1}`,
    backgroundColor: tokens.colorNeutralBackground1,
    // 移动端安全区域适配
    paddingTop: `max(${tokens.spacingVerticalS}, env(safe-area-inset-top))`,
    '@media (max-width: 480px)': {
      padding: `${tokens.spacingVerticalXS} ${tokens.spacingHorizontalS}`,
      paddingTop: `max(${tokens.spacingVerticalXS}, env(safe-area-inset-top))`,
    },
  },
  title: {
    marginLeft: tokens.spacingHorizontalM,
    fontSize: tokens.fontSizeBase400,
    fontWeight: tokens.fontWeightSemibold,
    '@media (max-width: 480px)': {
      marginLeft: tokens.spacingHorizontalS,
      fontSize: tokens.fontSizeBase300,
    },
  },
  leftSection: {
    display: 'flex',
    alignItems: 'center',
  },
  rightSection: {
    display: 'flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalS,
    '@media (max-width: 480px)': {
      gap: tokens.spacingHorizontalXS,
    },
  },
  newChatButton: {
    // 在桌面端隐藏（因为侧边栏有新建按钮）
    '@media (min-width: 769px)': {
      display: 'none',
    },
  },
})

export default function Header() {
  const classes = useStyles()
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const user = useAppSelector(selectUser)
  const theme = useAppSelector((state) => state.ui.theme)
  const { showSuccess, showError } = useToast()

  const handleLogout = () => {
    dispatch(logout())
  }

  const handleNewConversation = async () => {
    try {
      const result = await dispatch(createConversation({ title: '新对话' })).unwrap()
      navigate(`/chat/${result.id}`)
      showSuccess('创建成功', '新对话已创建')
    } catch (error) {
      console.error('Failed to create conversation:', error)
      showError('创建失败', '无法创建新对话，请重试')
    }
  }

  return (
    <header className={classes.header}>
      <div className={classes.leftSection}>
        <ToolbarButton
          icon={<NavigationRegular />}
          onClick={() => dispatch(toggleSidebar())}
          aria-label="切换侧边栏"
        />
        <span className={classes.title}>AI Chat</span>
      </div>

      <div className={classes.rightSection}>
        <Tooltip content="新建对话" relationship="label">
          <ToolbarButton
            icon={<AddRegular />}
            onClick={handleNewConversation}
            aria-label="新建对话"
            className={classes.newChatButton}
          />
        </Tooltip>

        <ToolbarButton
          icon={theme === 'dark' ? <WeatherSunnyRegular /> : <WeatherMoonRegular />}
          onClick={() => dispatch(toggleTheme())}
          aria-label="切换主题"
        />

        <Menu>
          <MenuTrigger disableButtonEnhancement>
            <ToolbarButton>
              <Avatar
                name={user?.username || 'User'}
                size={28}
                color="brand"
              />
            </ToolbarButton>
          </MenuTrigger>
          <MenuPopover>
            <MenuList>
              <MenuItem icon={<PersonRegular />}>
                {user?.username || '用户'}
              </MenuItem>
              <MenuItem icon={<SettingsRegular />}>设置</MenuItem>
              <ToolbarDivider />
              <MenuItem icon={<SignOutRegular />} onClick={handleLogout}>
                退出登录
              </MenuItem>
            </MenuList>
          </MenuPopover>
        </Menu>
      </div>
    </header>
  )
}