import { makeStyles, tokens, Avatar, Text } from '@fluentui/react-components'
import { Person24Regular, Bot24Regular } from '@fluentui/react-icons'
import type { Message } from '../../types'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    gap: tokens.spacingHorizontalM,
    padding: tokens.spacingVerticalM,
    borderRadius: tokens.borderRadiusMedium,
  },
  userMessage: {
    backgroundColor: tokens.colorNeutralBackground3,
  },
  assistantMessage: {
    backgroundColor: tokens.colorNeutralBackground1,
  },
  avatar: {
    flexShrink: 0,
  },
  content: {
    flex: 1,
    overflow: 'hidden',
    '& p': {
      margin: 0,
      marginBottom: tokens.spacingVerticalS,
      '&:last-child': {
        marginBottom: 0,
      },
    },
    '& pre': {
      margin: 0,
      marginBottom: tokens.spacingVerticalS,
      borderRadius: tokens.borderRadiusSmall,
      overflow: 'auto',
    },
    '& code': {
      fontFamily: 'Consolas, Monaco, monospace',
      fontSize: '14px',
    },
    '& ul, & ol': {
      marginTop: 0,
      marginBottom: tokens.spacingVerticalS,
      paddingLeft: '20px',
    },
    '& a': {
      color: tokens.colorBrandForeground1,
      textDecoration: 'none',
      '&:hover': {
        textDecoration: 'underline',
      },
    },
  },
  streamingCursor: {
    display: 'inline-block',
    width: '8px',
    height: '16px',
    backgroundColor: tokens.colorBrandForeground1,
    marginLeft: '2px',
    animation: 'blink 1s infinite',
    '@keyframes blink': {
      '0%, 100%': { opacity: 1 },
      '50%': { opacity: 0 },
    },
  },
  fileAttachments: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: tokens.spacingHorizontalS,
    marginTop: tokens.spacingVerticalS,
  },
  fileChip: {
    display: 'flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalXS,
    padding: `${tokens.spacingVerticalXS} ${tokens.spacingHorizontalS}`,
    backgroundColor: tokens.colorNeutralBackground4,
    borderRadius: tokens.borderRadiusSmall,
    fontSize: '12px',
  },
  imagePreview: {
    maxWidth: '300px',
    maxHeight: '200px',
    borderRadius: tokens.borderRadiusSmall,
    marginTop: tokens.spacingVerticalS,
  },
})

interface MessageItemProps {
  message: Message
  isStreaming?: boolean
}

export default function MessageItem({ message, isStreaming }: MessageItemProps) {
  const classes = useStyles()

  const isUser = message.role === 'user'

  return (
    <div
      className={`${classes.container} ${
        isUser ? classes.userMessage : classes.assistantMessage
      }`}
    >
      <Avatar
        className={classes.avatar}
        size={32}
        icon={isUser ? <Person24Regular /> : <Bot24Regular />}
        color={isUser ? 'brand' : 'colorful'}
      />

      <div className={classes.content}>
        <Text weight="semibold" size={200} block style={{ marginBottom: '4px' }}>
          {isUser ? '你' : 'AI 助手'}
        </Text>

        <ReactMarkdown
          components={{
            code({ node, className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || '')
              const inline = !match

              return inline ? (
                <code className={className} {...props}>
                  {children}
                </code>
              ) : (
                <SyntaxHighlighter
                  style={vscDarkPlus}
                  language={match[1]}
                  PreTag="div"
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              )
            },
          }}
        >
          {message.content}
        </ReactMarkdown>

        {isStreaming && <span className={classes.streamingCursor} />}

        {/* File attachments */}
        {message.attachments && message.attachments.length > 0 && (
          <div className={classes.fileAttachments}>
            {message.attachments.map((attachment) => (
              <div key={attachment.id}>
                {attachment.type === 'image' ? (
                  <img
                    src={attachment.url}
                    alt={attachment.fileName || 'image'}
                    className={classes.imagePreview}
                  />
                ) : (
                  <div className={classes.fileChip}>
                    📎 {attachment.fileName}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}