import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  makeStyles,
  tokens,
  Button,
  Dialog,
  DialogTrigger,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogActions,
  DialogContent,
  Input,
} from '@fluentui/react-components'
import { AddRegular, ArrowSyncRegular } from '@fluentui/react-icons'

import { useAppDispatch, useAppSelector } from '../../hooks/useAppDispatch'
import {
  fetchConversations,
  createConversation,
  renameConversation,
  deleteConversation,
  setCurrentConversation,
} from '../../features/conversations/conversationsSlice'
import { closeSidebarOnMobile } from '../../features/ui/uiSlice'
import ConversationList from './ConversationList'
import { SidebarSkeleton } from '../Skeleton'
import { useToast } from '../Toast'

const useStyles = makeStyles({
  sidebar: {
    width: '280px',
    minWidth: '280px',
    maxWidth: '100vw', // 移动端不超过屏幕宽度
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: tokens.colorNeutralBackground3,
    borderRight: `1px solid ${tokens.colorNeutralStroke1}`,
    // 移动端响应式
    '@media (max-width: 768px)': {
      width: '85vw',
      minWidth: 'auto',
      maxWidth: '320px',
    },
  },
  header: {
    padding: tokens.spacingVerticalM,
    borderBottom: `1px solid ${tokens.colorNeutralStroke1}`,
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalS,
  },
  headerButtons: {
    display: 'flex',
    gap: tokens.spacingHorizontalS,
  },
  newButton: {
    flex: 1,
  },
  refreshButton: {
    minWidth: 'auto',
  },
  content: {
    flex: 1,
    overflow: 'auto',
    padding: tokens.spacingVerticalS,
  },
  loading: {
    display: 'flex',
    justifyContent: 'center',
    padding: tokens.spacingVerticalXXL,
  },
})

export default function Sidebar() {
  const classes = useStyles()
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()

  const { items, isLoading, currentId, hasFetched } = useAppSelector(
    (state) => state.conversations
  )
  const isAuthenticated = useAppSelector((state) => !!state.auth.token)

  // State for rename dialog
  const [renameDialogOpen, setRenameDialogOpen] = useState(false)
  const [renameId, setRenameId] = useState<string | null>(null)
  const [renameTitle, setRenameTitle] = useState('')

  // State for delete confirmation dialog
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteId, setDeleteId] = useState<string | null>(null)

  // Fetch conversations only on first load (when not fetched yet)
  useEffect(() => {
    if (isAuthenticated && !hasFetched) {
      dispatch(fetchConversations())
    }
  }, [isAuthenticated, hasFetched, dispatch])

  // Manual refresh handler
  const handleRefresh = () => {
    dispatch(fetchConversations())
  }

  const handleNewConversation = async () => {
    try {
      const result = await dispatch(createConversation({ title: '新对话' })).unwrap()
      navigate(`/chat/${result.id}`)
      // 移动端创建后自动关闭侧边栏
      dispatch(closeSidebarOnMobile())
      showSuccess('创建成功', '新对话已创建')
    } catch (error) {
      console.error('Failed to create conversation:', error)
      showError('创建失败', '无法创建新对话，请重试')
    }
  }

  const handleSelectConversation = (id: string) => {
    dispatch(setCurrentConversation(id))
    navigate(`/chat/${id}`)
    // 移动端选择后自动关闭侧边栏
    dispatch(closeSidebarOnMobile())
  }

  const handleRenameClick = (id: string, title: string) => {
    setRenameId(id)
    setRenameTitle(title)
    setRenameDialogOpen(true)
  }

  const handleRenameConfirm = async () => {
    if (!renameId || !renameTitle.trim()) return

    try {
      await dispatch(renameConversation({ id: renameId, title: renameTitle.trim() })).unwrap()
      showSuccess('重命名成功')
    } catch (error) {
      console.error('Failed to rename conversation:', error)
      showError('重命名失败', '无法重命名对话，请重试')
    } finally {
      setRenameDialogOpen(false)
      setRenameId(null)
      setRenameTitle('')
    }
  }

  const handleDeleteClick = (id: string) => {
    setDeleteId(id)
    setDeleteDialogOpen(true)
  }

  const handleDeleteConfirm = async () => {
    if (!deleteId) return

    const wasCurrentConversation = currentId === deleteId

    try {
      await dispatch(deleteConversation(deleteId)).unwrap()
      // If we deleted the current conversation, navigate to home
      if (wasCurrentConversation) {
        navigate('/')
      }
      showSuccess('删除成功', '对话已删除')
    } catch (error) {
      console.error('Failed to delete conversation:', error)
      showError('删除失败', '无法删除对话，请重试')
    } finally {
      setDeleteDialogOpen(false)
      setDeleteId(null)
    }
  }

  return (
    <aside className={classes.sidebar}>
      <div className={classes.header}>
        <div className={classes.headerButtons}>
          <Button
            appearance="primary"
            icon={<AddRegular />}
            onClick={handleNewConversation}
            className={classes.newButton}
          >
            新建对话
          </Button>
          <Button
            appearance="subtle"
            icon={<ArrowSyncRegular />}
            onClick={handleRefresh}
            disabled={isLoading}
            className={classes.refreshButton}
            title="刷新对话列表"
          />
        </div>
      </div>

      <div className={classes.content}>
        {isLoading ? (
          <SidebarSkeleton />
        ) : (
          <ConversationList
            conversations={items}
            currentId={currentId}
            onSelect={handleSelectConversation}
            onRename={handleRenameClick}
            onDelete={handleDeleteClick}
          />
        )}
      </div>

      {/* Rename Dialog */}
      <Dialog open={renameDialogOpen} onOpenChange={(_, data) => setRenameDialogOpen(data.open)}>
        <DialogSurface>
          <DialogBody>
            <DialogTitle>重命名对话</DialogTitle>
            <DialogContent>
              <Input
                value={renameTitle}
                onChange={(_, data) => setRenameTitle(data.value)}
                placeholder="输入新名称"
                style={{ width: '100%', marginTop: '8px' }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleRenameConfirm()
                  }
                }}
              />
            </DialogContent>
            <DialogActions>
              <DialogTrigger disableButtonEnhancement>
                <Button appearance="secondary">取消</Button>
              </DialogTrigger>
              <Button appearance="primary" onClick={handleRenameConfirm}>
                确定
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={(_, data) => setDeleteDialogOpen(data.open)}>
        <DialogSurface>
          <DialogBody>
            <DialogTitle>删除对话</DialogTitle>
            <DialogContent>
              确定要删除这个对话吗？此操作无法撤销。
            </DialogContent>
            <DialogActions>
              <DialogTrigger disableButtonEnhancement>
                <Button appearance="secondary">取消</Button>
              </DialogTrigger>
              <Button appearance="primary" onClick={handleDeleteConfirm}>
                删除
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>
    </aside>
  )
}