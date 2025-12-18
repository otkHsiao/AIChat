import { useEffect, useRef, useState } from 'react'
import { makeStyles, tokens, Text } from '@fluentui/react-components'

import { useAppDispatch, useAppSelector } from '../../store'
import { setMessages, clearMessages } from '../../features/chat/chatSlice'
import { useStreamingChat } from '../../hooks/useStreamingChat'
import MessageList from './MessageList'
import MessageInput from './MessageInput'
import { ChatSkeleton } from '../Skeleton'
import { useToast } from '../Toast'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    overflow: 'hidden',
  },
  messageArea: {
    flex: 1,
    overflow: 'auto',
    padding: tokens.spacingVerticalL,
    // 移动端适配
    '@media (max-width: 768px)': {
      padding: tokens.spacingVerticalM,
    },
    '@media (max-width: 480px)': {
      padding: tokens.spacingVerticalS,
    },
  },
  inputArea: {
    padding: tokens.spacingVerticalM,
    borderTop: `1px solid ${tokens.colorNeutralStroke1}`,
    backgroundColor: tokens.colorNeutralBackground1,
    // 移动端适配 - 增加底部安全区域
    '@media (max-width: 768px)': {
      padding: `${tokens.spacingVerticalS} ${tokens.spacingHorizontalS}`,
      paddingBottom: `max(${tokens.spacingVerticalS}, env(safe-area-inset-bottom))`,
    },
  },
  emptyState: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    color: tokens.colorNeutralForeground3,
    gap: tokens.spacingVerticalM,
    padding: tokens.spacingHorizontalL,
    textAlign: 'center',
    // 移动端适配
    '@media (max-width: 480px)': {
      padding: tokens.spacingHorizontalM,
    },
  },
  loading: {
    display: 'flex',
    justifyContent: 'center',
    padding: tokens.spacingVerticalXXL,
  },
})

export default function ChatContainer() {
  const classes = useStyles()
  const dispatch = useAppDispatch()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [isLoadingMessages, setIsLoadingMessages] = useState(false)
  const { showError } = useToast()

  const currentId = useAppSelector((state) => state.conversations.currentId)
  const { messages, isStreaming, streamingContent, error } = useAppSelector(
    (state) => state.chat
  )
  const token = useAppSelector((state) => state.auth.token)

  // Initialize streaming chat hook
  const { sendMessage } = useStreamingChat({
    conversationId: currentId || '',
  })

  // Fetch messages when conversation changes
  useEffect(() => {
    const fetchMessages = async () => {
      if (!currentId || !token) {
        dispatch(clearMessages())
        return
      }

      setIsLoadingMessages(true)
      try {
        const response = await fetch(
          `${API_BASE_URL}/conversations/${currentId}/messages`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        )
        const data = await response.json()
        if (data.success && data.data) {
          dispatch(setMessages(data.data.messages))
        }
      } catch (err) {
        console.error('Failed to fetch messages:', err)
        showError('加载失败', '无法加载消息历史')
      } finally {
        setIsLoadingMessages(false)
      }
    }

    fetchMessages()
  }, [currentId, token, dispatch, showError])

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  // No conversation selected
  if (!currentId) {
    return (
      <div className={classes.container}>
        <div className={classes.emptyState}>
          <Text size={500} weight="semibold">
            选择或创建一个对话开始聊天
          </Text>
          <Text size={300}>
            点击左侧"新建对话"按钮创建新的对话
          </Text>
        </div>
      </div>
    )
  }

  return (
    <div className={classes.container}>
      <div className={classes.messageArea}>
        {isLoadingMessages ? (
          <ChatSkeleton />
        ) : (
          <MessageList
            messages={messages}
            isStreaming={isStreaming}
            streamingContent={streamingContent}
          />
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className={classes.inputArea}>
        <MessageInput
          onSend={(content, files) => sendMessage({ content, files })}
          disabled={isStreaming || isLoadingMessages}
        />
        {error && (
          <Text style={{ color: tokens.colorPaletteRedForeground1, marginTop: 8 }}>
            {error}
          </Text>
        )}
      </div>
    </div>
  )
}