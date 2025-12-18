import { makeStyles, tokens } from '@fluentui/react-components'
import type { Message } from '../../types'
import MessageItem from './MessageItem'

const useStyles = makeStyles({
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalL,
    maxWidth: '800px',
    margin: '0 auto',
    width: '100%',
    boxSizing: 'border-box',
    // 移动端适配
    '@media (max-width: 768px)': {
      gap: tokens.spacingVerticalM,
      maxWidth: '100%',
    },
    '@media (max-width: 480px)': {
      gap: tokens.spacingVerticalS,
    },
  },
})

interface MessageListProps {
  messages: Message[]
  isStreaming: boolean
  streamingContent: string
}

export default function MessageList({
  messages,
  isStreaming,
  streamingContent,
}: MessageListProps) {
  const classes = useStyles()

  return (
    <div className={classes.list}>
      {messages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}

      {/* Show streaming message */}
      {isStreaming && streamingContent && (
        <MessageItem
          message={{
            id: 'streaming',
            conversationId: '',
            role: 'assistant',
            content: streamingContent,
            createdAt: new Date().toISOString(),
          }}
          isStreaming
        />
      )}
    </div>
  )
}