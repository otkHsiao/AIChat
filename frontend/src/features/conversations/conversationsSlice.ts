import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { Conversation } from '../../types'

interface ConversationsState {
  items: Conversation[]
  currentId: string | null
  isLoading: boolean
  error: string | null
  total: number
}

const initialState: ConversationsState = {
  items: [],
  currentId: null,
  isLoading: false,
  error: null,
  total: 0,
}

const conversationsSlice = createSlice({
  name: 'conversations',
  initialState,
  reducers: {
    setConversations: (
      state,
      action: PayloadAction<{ items: Conversation[]; total: number }>
    ) => {
      state.items = action.payload.items
      state.total = action.payload.total
      state.isLoading = false
      state.error = null
    },

    addConversation: (state, action: PayloadAction<Conversation>) => {
      state.items.unshift(action.payload)
      state.total += 1
    },

    updateConversation: (
      state,
      action: PayloadAction<{ id: string; updates: Partial<Conversation> }>
    ) => {
      const index = state.items.findIndex(
        (conv) => conv.id === action.payload.id
      )
      if (index !== -1) {
        state.items[index] = {
          ...state.items[index],
          ...action.payload.updates,
        }
      }
    },

    removeConversation: (state, action: PayloadAction<string>) => {
      state.items = state.items.filter((conv) => conv.id !== action.payload)
      state.total -= 1
      if (state.currentId === action.payload) {
        state.currentId = null
      }
    },

    setCurrentConversation: (state, action: PayloadAction<string | null>) => {
      state.currentId = action.payload
    },

    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },

    setError: (state, action: PayloadAction<string>) => {
      state.error = action.payload
      state.isLoading = false
    },

    clearConversations: (state) => {
      state.items = []
      state.currentId = null
      state.total = 0
      state.error = null
    },
  },
})

export const {
  setConversations,
  addConversation,
  updateConversation,
  removeConversation,
  setCurrentConversation,
  setLoading,
  setError,
  clearConversations,
} = conversationsSlice.actions

export default conversationsSlice.reducer