import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { Message } from '../../types'

interface ChatState {
  messages: Message[]
  isStreaming: boolean
  streamingContent: string
  error: string | null
}

const initialState: ChatState = {
  messages: [],
  isStreaming: false,
  streamingContent: '',
  error: null,
}

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    setMessages: (state, action: PayloadAction<Message[]>) => {
      state.messages = action.payload
      state.error = null
    },

    addMessage: (state, action: PayloadAction<Message>) => {
      state.messages.push(action.payload)
    },

    updateMessage: (
      state,
      action: PayloadAction<{ id: string; updates: Partial<Message> }>
    ) => {
      const index = state.messages.findIndex(
        (msg) => msg.id === action.payload.id
      )
      if (index !== -1) {
        state.messages[index] = {
          ...state.messages[index],
          ...action.payload.updates,
        }
      }
    },

    startStreaming: (state) => {
      state.isStreaming = true
      state.streamingContent = ''
      state.error = null
    },

    appendStreamingContent: (state, action: PayloadAction<string>) => {
      state.streamingContent += action.payload
    },

    endStreaming: (state, action: PayloadAction<Message | undefined>) => {
      state.isStreaming = false
      if (action.payload) {
        state.messages.push(action.payload)
      }
      state.streamingContent = ''
    },

    cancelStreaming: (state) => {
      state.isStreaming = false
      state.streamingContent = ''
    },

    setError: (state, action: PayloadAction<string>) => {
      state.error = action.payload
      state.isStreaming = false
    },

    clearMessages: (state) => {
      state.messages = []
      state.streamingContent = ''
      state.error = null
    },
  },
})

export const {
  setMessages,
  addMessage,
  updateMessage,
  startStreaming,
  appendStreamingContent,
  endStreaming,
  cancelStreaming,
  setError,
  clearMessages,
} = chatSlice.actions

export default chatSlice.reducer