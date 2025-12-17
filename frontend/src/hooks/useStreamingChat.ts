import { useCallback, useRef } from 'react'
import { useAppDispatch, useAppSelector } from '../store'
import {
  startStreaming,
  appendStreamingContent,
  endStreaming,
  cancelStreaming,
  addMessage,
  setError,
} from '../features/chat/chatSlice'
import type { Message, TokenUsage } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

interface UseStreamingChatOptions {
  conversationId: string
  onMessageComplete?: (message: Message) => void
}

interface SendMessageOptions {
  content: string
  files?: File[]
}

export function useStreamingChat({
  conversationId,
  onMessageComplete,
}: UseStreamingChatOptions) {
  const dispatch = useAppDispatch()
  const token = useAppSelector((state) => state.auth.token)
  const abortControllerRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(
    async ({ content, files }: SendMessageOptions) => {
      if (!conversationId || !token) {
        dispatch(setError('No conversation selected or not authenticated'))
        return
      }

      // Abort any existing stream
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }

      const abortController = new AbortController()
      abortControllerRef.current = abortController

      // Add user message to state
      const userMessage: Message = {
        id: `temp-${Date.now()}`,
        conversationId,
        role: 'user',
        content,
        createdAt: new Date().toISOString(),
      }
      dispatch(addMessage(userMessage))

      // Reset streaming state
      dispatch(startStreaming())

      try {
        // Prepare request body
        const body = JSON.stringify({
          content,
          attachments: files?.map((f) => ({ id: f.name, type: 'file' })) || [],
        })

        // Start SSE connection
        const response = await fetch(
          `${API_BASE_URL}/conversations/${conversationId}/messages/stream`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`,
            },
            body,
            signal: abortController.signal,
          }
        )

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw new Error(errorData.message || 'Failed to send message')
        }

        // Process SSE stream
        const reader = response.body?.getReader()
        if (!reader) {
          throw new Error('No response body')
        }

        const decoder = new TextDecoder()
        let buffer = ''
        let fullContent = ''
        let messageId = ''
        let tokens: TokenUsage | undefined
        let currentEventType = ''

        while (true) {
          const { done, value } = await reader.read()

          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // Process SSE events
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            // Handle event type line
            if (line.startsWith('event: ')) {
              currentEventType = line.slice(7).trim()
              continue
            }

            if (line.startsWith('data: ')) {
              const data = line.slice(6)

              if (data === '[DONE]') {
                break
              }

              try {
                const eventData = JSON.parse(data)

                // Use the event type from the event: line, or from eventData.type if present
                const eventType = currentEventType || eventData.type

                switch (eventType) {
                  case 'message_start':
                    messageId = eventData.messageId || eventData.userMessageId || ''
                    break

                  case 'content_delta':
                    const delta = eventData.delta
                    if (delta) {
                      fullContent += delta
                      dispatch(appendStreamingContent(delta))
                    }
                    break

                  case 'message_end':
                    messageId = eventData.messageId || messageId
                    tokens = eventData.tokens
                    break

                  case 'error':
                    throw new Error(eventData.error)
                }

                // Reset event type after processing
                currentEventType = ''
              } catch (e) {
                // Ignore JSON parse errors for incomplete chunks
                if (e instanceof SyntaxError) continue
                throw e
              }
            }
          }
        }

        // Finalize message
        const assistantMessage: Message = {
          id: messageId || `msg-${Date.now()}`,
          conversationId,
          role: 'assistant',
          content: fullContent,
          tokens,
          createdAt: new Date().toISOString(),
        }

        dispatch(endStreaming(assistantMessage))

        onMessageComplete?.(assistantMessage)
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          // Request was aborted, ignore
          return
        }

        const errorMessage =
          error instanceof Error ? error.message : 'An error occurred'
        dispatch(setError(errorMessage))
      } finally {
        abortControllerRef.current = null
      }
    },
    [conversationId, token, dispatch, onMessageComplete]
  )

  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
      dispatch(cancelStreaming())
    }
  }, [dispatch])

  return {
    sendMessage,
    stopStreaming,
  }
}

export default useStreamingChat