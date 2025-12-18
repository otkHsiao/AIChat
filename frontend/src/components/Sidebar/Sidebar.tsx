import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  makeStyles,
  tokens,
  Button,
  Spinner,
  Dialog,
  DialogTrigger,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogActions,
  DialogContent,
  Input,
} from '@fluentui/react-components'
import { AddRegular } from '@fluentui/react-icons'

import { useAppDispatch, useAppSelector } from '../../hooks/useAppDispatch'
import {
  fetchConversations,
  createConversation,
  renameConversation,
  deleteConversation,
  setCurrentConversation,
} from '../../features/conversations/conversationsSlice'
import ConversationList from './ConversationList'

const useStyles = makeStyles({
  sidebar: {
    width: '280px',
    minWidth: '280px',
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: tokens.colorNeutralBackground3,
    borderRight: `1px solid ${tokens.colorNeutralStroke1}`,
  },
  header: {
    padding: tokens.spacingVerticalM,
    borderBottom: `1px solid ${tokens.colorNeutralStroke1}`,
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

  const { items, isLoading, currentId } = useAppSelector(
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

  // Fetch conversations on mount
  useEffect(() => {
    if (isAuthenticated) {
      dispatch(fetchConversations())
    }
  }, [isAuthenticated, dispatch])

  const handleNewConversation = async () => {
    try {
      const result = await dispatch(createConversation({ title: '新对话' })).unwrap()
      navigate(`/chat/${result.id}`)
    } catch (error) {
      console.error('Failed to create conversation:', error)
    }
  }

  const handleSelectConversation = (id: string) => {
    dispatch(setCurrentConversation(id))
    navigate(`/chat/${id}`)
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
    } catch (error) {
      console.error('Failed to rename conversation:', error)
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
    } catch (error) {
      console.error('Failed to delete conversation:', error)
    } finally {
      setDeleteDialogOpen(false)
      setDeleteId(null)
    }
  }

  return (
    <aside className={classes.sidebar}>
      <div className={classes.header}>
        <Button
          appearance="primary"
          icon={<AddRegular />}
          onClick={handleNewConversation}
          style={{ width: '100%' }}
        >
          新建对话
        </Button>
      </div>

      <div className={classes.content}>
        {isLoading ? (
          <div className={classes.loading}>
            <Spinner size="small" />
          </div>
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