import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  makeStyles,
  tokens,
  Button,
  Spinner,
} from '@fluentui/react-components'
import { AddRegular } from '@fluentui/react-icons'

import { useAppDispatch, useAppSelector } from '../../hooks/useAppDispatch'
import {
  setConversations,
  setCurrentConversation,
  addConversation,
  setLoading,
} from '../../features/conversations/conversationsSlice'
import ConversationList from './ConversationList'
import type { Conversation } from '../../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

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
  const token = useAppSelector((state) => state.auth.token)

  // Fetch conversations on mount
  useEffect(() => {
    const fetchConversations = async () => {
      if (!token) return

      dispatch(setLoading(true))
      try {
        const response = await fetch(`${API_BASE_URL}/conversations`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
        const data = await response.json()
        if (data.success && data.data) {
          dispatch(
            setConversations({
              items: data.data.conversations,
              total: data.data.total,
            })
          )
        }
      } catch (error) {
        console.error('Failed to fetch conversations:', error)
      }
    }

    fetchConversations()
  }, [token, dispatch])

  const handleNewConversation = async () => {
    if (!token) return

    try {
      const response = await fetch(`${API_BASE_URL}/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: '新对话',
        }),
      })
      const data = await response.json()
      if (data.success && data.data) {
        const newConversation: Conversation = data.data
        dispatch(addConversation(newConversation))
        dispatch(setCurrentConversation(newConversation.id))
        navigate(`/chat/${newConversation.id}`)
      }
    } catch (error) {
      console.error('Failed to create conversation:', error)
    }
  }

  const handleSelectConversation = (id: string) => {
    dispatch(setCurrentConversation(id))
    navigate(`/chat/${id}`)
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
          />
        )}
      </div>
    </aside>
  )
}