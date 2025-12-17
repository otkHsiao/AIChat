/**
 * User related types
 */
export interface User {
  id: string
  email: string
  username: string
  createdAt: string
  settings?: UserSettings
}

export interface UserSettings {
  defaultModel: string
  theme: 'light' | 'dark'
}

/**
 * Authentication related types
 */
export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  username: string
  password: string
}

export interface AuthResponse {
  user: User
  accessToken: string
  refreshToken: string
  expiresIn: number
}

/**
 * Conversation related types
 */
export interface Conversation {
  id: string
  userId: string
  title: string
  systemPrompt: string
  model: string
  messageCount: number
  createdAt: string
  updatedAt: string
}

export interface ConversationCreate {
  title?: string
  systemPrompt?: string
  model?: string
}

export interface ConversationUpdate {
  title?: string
  systemPrompt?: string
  model?: string
}

/**
 * Message related types
 */
export interface Message {
  id: string
  conversationId: string
  role: 'user' | 'assistant' | 'system'
  content: string
  attachments?: Attachment[]
  tokens?: TokenUsage
  createdAt: string
}

export interface Attachment {
  id: string
  type: 'image' | 'file'
  fileName?: string
  url?: string
  mimeType?: string
  size?: number
}

export interface AttachmentRef {
  id: string
  type: 'image' | 'file'
}

export interface TokenUsage {
  input: number
  output: number
}

export interface MessageCreate {
  content: string
  attachments?: AttachmentRef[]
}

/**
 * File related types
 */
export interface FileUpload {
  id: string
  fileName: string
  type: 'image' | 'file'
  mimeType: string
  size: number
  url: string
  createdAt: string
}

/**
 * API response types
 */
export interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
  error?: ApiError
}

export interface ApiError {
  code: string
  message: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
  hasMore?: boolean
}

/**
 * SSE event types for streaming
 */
export interface StreamMessageStart {
  messageId?: string
  userMessageId?: string
}

export interface StreamContentDelta {
  delta: string
}

export interface StreamMessageEnd {
  messageId: string
  tokens: TokenUsage
}

export interface StreamError {
  error: string
}

export type StreamEvent =
  | { type: 'message_start'; data: StreamMessageStart }
  | { type: 'content_delta'; data: StreamContentDelta }
  | { type: 'message_end'; data: StreamMessageEnd }
  | { type: 'error'; data: StreamError }