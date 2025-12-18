import { useState, useRef, KeyboardEvent } from 'react'
import {
  makeStyles,
  tokens,
  Textarea,
  Button,
  Tooltip,
} from '@fluentui/react-components'
import {
  Send24Regular,
  Attach24Regular,
  Image24Regular,
  Dismiss24Regular,
} from '@fluentui/react-icons'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalS,
    maxWidth: '800px',
    margin: '0 auto',
    width: '100%',
    padding: `0 ${tokens.spacingHorizontalS}`,
    boxSizing: 'border-box',
    // 移动端适配
    '@media (max-width: 768px)': {
      padding: `0 ${tokens.spacingHorizontalXS}`,
    },
  },
  inputRow: {
    display: 'flex',
    gap: tokens.spacingHorizontalS,
    alignItems: 'flex-end',
    // 移动端适配
    '@media (max-width: 480px)': {
      gap: tokens.spacingHorizontalXS,
    },
  },
  textareaWrapper: {
    flex: 1,
    position: 'relative',
    minWidth: 0, // 允许 flex 收缩
  },
  textarea: {
    width: '100%',
    minHeight: '56px',
    maxHeight: '200px',
    resize: 'none',
    // 移动端适配
    '@media (max-width: 480px)': {
      minHeight: '44px',
      fontSize: '16px', // 防止 iOS 自动缩放
    },
  },
  actions: {
    display: 'flex',
    gap: tokens.spacingHorizontalXS,
    alignItems: 'center',
    flexShrink: 0,
    // 移动端适配：隐藏文字只显示图标
    '@media (max-width: 480px)': {
      gap: '2px',
    },
  },
  attachments: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: tokens.spacingHorizontalS,
    // 移动端适配
    '@media (max-width: 480px)': {
      gap: tokens.spacingHorizontalXS,
    },
  },
  attachmentChip: {
    display: 'flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalXS,
    padding: `${tokens.spacingVerticalXS} ${tokens.spacingHorizontalS}`,
    backgroundColor: tokens.colorNeutralBackground4,
    borderRadius: tokens.borderRadiusSmall,
    fontSize: '12px',
    maxWidth: '150px',
    overflow: 'hidden',
  },
  imagePreview: {
    width: '60px',
    height: '60px',
    objectFit: 'cover',
    borderRadius: tokens.borderRadiusSmall,
    // 移动端适配
    '@media (max-width: 480px)': {
      width: '48px',
      height: '48px',
    },
  },
  removeButton: {
    minWidth: 'auto',
    padding: '2px',
  },
  hint: {
    fontSize: '12px',
    color: tokens.colorNeutralForeground3,
    textAlign: 'center',
    // 移动端隐藏提示
    '@media (max-width: 480px)': {
      display: 'none',
    },
  },
  // 移动端发送按钮样式
  sendButton: {
    '@media (max-width: 480px)': {
      minWidth: 'auto',
      paddingLeft: tokens.spacingHorizontalS,
      paddingRight: tokens.spacingHorizontalS,
    },
  },
  // 移动端隐藏按钮文字
  sendButtonText: {
    '@media (max-width: 480px)': {
      display: 'none',
    },
  },
})

interface FileAttachment {
  file: File
  preview?: string
}

interface MessageInputProps {
  onSend: (content: string, files?: File[]) => void
  disabled?: boolean
}

export default function MessageInput({ onSend, disabled }: MessageInputProps) {
  const classes = useStyles()
  const [content, setContent] = useState('')
  const [attachments, setAttachments] = useState<FileAttachment[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)
  const imageInputRef = useRef<HTMLInputElement>(null)

  const handleSend = () => {
    if (!content.trim() && attachments.length === 0) return

    const files = attachments.map((a) => a.file)
    onSend(content, files.length > 0 ? files : undefined)
    setContent('')
    setAttachments([])
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleFileSelect = (files: FileList | null, _type: 'file' | 'image') => {
    if (!files) return

    const newAttachments: FileAttachment[] = []

    Array.from(files).forEach((file) => {
      const attachment: FileAttachment = { file }

      // Create preview for images
      if (file.type.startsWith('image/')) {
        attachment.preview = URL.createObjectURL(file)
      }

      newAttachments.push(attachment)
    })

    setAttachments((prev) => [...prev, ...newAttachments])
  }

  const removeAttachment = (index: number) => {
    setAttachments((prev) => {
      const attachment = prev[index]
      if (attachment.preview) {
        URL.revokeObjectURL(attachment.preview)
      }
      return prev.filter((_, i) => i !== index)
    })
  }

  return (
    <div className={classes.container}>
      {/* Attachments preview */}
      {attachments.length > 0 && (
        <div className={classes.attachments}>
          {attachments.map((attachment, index) => (
            <div key={index} className={classes.attachmentChip}>
              {attachment.preview ? (
                <img
                  src={attachment.preview}
                  alt={attachment.file.name}
                  className={classes.imagePreview}
                />
              ) : (
                <span>📎 {attachment.file.name}</span>
              )}
              <Button
                className={classes.removeButton}
                appearance="subtle"
                size="small"
                icon={<Dismiss24Regular />}
                onClick={() => removeAttachment(index)}
              />
            </div>
          ))}
        </div>
      )}

      <div className={classes.inputRow}>
        <div className={classes.textareaWrapper}>
          <Textarea
            className={classes.textarea}
            placeholder="输入消息... (Shift + Enter 换行)"
            value={content}
            onChange={(_e, data) => setContent(data.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            resize="vertical"
          />
        </div>

        <div className={classes.actions}>
          {/* Hidden file inputs */}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            style={{ display: 'none' }}
            onChange={(e) => handleFileSelect(e.target.files, 'file')}
          />
          <input
            ref={imageInputRef}
            type="file"
            accept="image/*"
            multiple
            style={{ display: 'none' }}
            onChange={(e) => handleFileSelect(e.target.files, 'image')}
          />

          <Tooltip content="附加文件" relationship="label">
            <Button
              appearance="subtle"
              icon={<Attach24Regular />}
              onClick={() => fileInputRef.current?.click()}
              disabled={disabled}
            />
          </Tooltip>

          <Tooltip content="上传图片" relationship="label">
            <Button
              appearance="subtle"
              icon={<Image24Regular />}
              onClick={() => imageInputRef.current?.click()}
              disabled={disabled}
            />
          </Tooltip>

          <Button
            appearance="primary"
            icon={<Send24Regular />}
            onClick={handleSend}
            disabled={disabled || (!content.trim() && attachments.length === 0)}
            className={classes.sendButton}
          >
            <span className={classes.sendButtonText}>发送</span>
          </Button>
        </div>
      </div>

      <div className={classes.hint}>
        按 Enter 发送，Shift + Enter 换行
      </div>
    </div>
  )
}