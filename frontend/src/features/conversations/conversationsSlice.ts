import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import type { Conversation } from '../../types'
import type { RootState } from '../../store'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// API response wrapper type
interface ApiResponse<T> {
  success: boolean
  data: T
}

// Conversation list response
interface ConversationListData {
  conversations: Conversation[]
  total: number
  limit: number
  offset: number
}

// ============ Async Thunks ============

// Fetch all conversations
export const fetchConversations = createAsyncThunk<
  { items: Conversation[]; total: number },
  { limit?: number; offset?: number } | void,
  { state: RootState; rejectValue: string }
>('conversations/fetchConversations', async (params, { getState, rejectWithValue }) => {
  const token = getState().auth.token
  if (!token) {
    return rejectWithValue('未登录')
  }

  // Handle both void and object params
  const paramsObj = params && typeof params === 'object' ? params : {}
  const limit = paramsObj.limit ?? 50
  const offset = paramsObj.offset ?? 0

  try {
    const response = await fetch(
      `${API_BASE_URL}/conversations?limit=${limit}&offset=${offset}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    )

    if (!response.ok) {
      throw new Error('获取对话列表失败')
    }

    const data: ApiResponse<ConversationListData> = await response.json()
    if (data.success && data.data) {
      return {
        items: data.data.conversations,
        total: data.data.total,
      }
    }
    throw new Error('获取对话列表失败')
  } catch (error) {
    return rejectWithValue(error instanceof Error ? error.message : '获取对话列表失败')
  }
})

// Create a new conversation
export const createConversation = createAsyncThunk<
  Conversation,
  { title?: string; systemPrompt?: string },
  { state: RootState; rejectValue: string }
>('conversations/createConversation', async (params, { getState, rejectWithValue }) => {
  const token = getState().auth.token
  if (!token) {
    return rejectWithValue('未登录')
  }

  try {
    const response = await fetch(`${API_BASE_URL}/conversations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        title: params.title ?? '新对话',
        systemPrompt: params.systemPrompt,
      }),
    })

    if (!response.ok) {
      throw new Error('创建对话失败')
    }

    const data: ApiResponse<Conversation> = await response.json()
    if (data.success && data.data) {
      return data.data
    }
    throw new Error('创建对话失败')
  } catch (error) {
    return rejectWithValue(error instanceof Error ? error.message : '创建对话失败')
  }
})

// Rename a conversation
export const renameConversation = createAsyncThunk<
  Conversation,
  { id: string; title: string },
  { state: RootState; rejectValue: string }
>('conversations/renameConversation', async ({ id, title }, { getState, rejectWithValue }) => {
  const token = getState().auth.token
  if (!token) {
    return rejectWithValue('未登录')
  }

  try {
    const response = await fetch(`${API_BASE_URL}/conversations/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ title }),
    })

    if (!response.ok) {
      throw new Error('重命名对话失败')
    }

    const data: ApiResponse<Conversation> = await response.json()
    if (data.success && data.data) {
      return data.data
    }
    throw new Error('重命名对话失败')
  } catch (error) {
    return rejectWithValue(error instanceof Error ? error.message : '重命名对话失败')
  }
})

// Delete a conversation
export const deleteConversation = createAsyncThunk<
  string,
  string,
  { state: RootState; rejectValue: string }
>('conversations/deleteConversation', async (id, { getState, rejectWithValue }) => {
  const token = getState().auth.token
  if (!token) {
    return rejectWithValue('未登录')
  }

  try {
    const response = await fetch(`${API_BASE_URL}/conversations/${id}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })

    if (!response.ok) {
      throw new Error('删除对话失败')
    }

    return id
  } catch (error) {
    return rejectWithValue(error instanceof Error ? error.message : '删除对话失败')
  }
})

// ============ Slice ============

interface ConversationsState {
  items: Conversation[]
  currentId: string | null
  isLoading: boolean
  error: string | null
  total: number
  hasFetched: boolean // 标记是否已经获取过数据
}

const initialState: ConversationsState = {
  items: [],
  currentId: null,
  isLoading: false,
  error: null,
  total: 0,
  hasFetched: false,
}

const conversationsSlice = createSlice({
  name: 'conversations',
  initialState,
  reducers: {
    setCurrentConversation: (state, action: PayloadAction<string | null>) => {
      state.currentId = action.payload
    },

    clearError: (state) => {
      state.error = null
    },

    clearConversations: (state) => {
      state.items = []
      state.currentId = null
      state.total = 0
      state.error = null
      state.hasFetched = false
    },

    updateConversationTitle: (state, action: PayloadAction<{ id: string; title: string }>) => {
      const conversation = state.items.find((conv) => conv.id === action.payload.id)
      if (conversation) {
        conversation.title = action.payload.title
        conversation.updatedAt = new Date().toISOString()
      }
    },
  },
  extraReducers: (builder) => {
    // Fetch conversations
    builder
      .addCase(fetchConversations.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchConversations.fulfilled, (state, action) => {
        state.items = action.payload.items
        state.total = action.payload.total
        state.isLoading = false
        state.error = null
        state.hasFetched = true
      })
      .addCase(fetchConversations.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload ?? '获取对话列表失败'
      })

    // Create conversation
    builder
      .addCase(createConversation.pending, (state) => {
        state.error = null
      })
      .addCase(createConversation.fulfilled, (state, action) => {
        state.items.unshift(action.payload)
        state.total += 1
        state.currentId = action.payload.id
      })
      .addCase(createConversation.rejected, (state, action) => {
        state.error = action.payload ?? '创建对话失败'
      })

    // Rename conversation
    builder
      .addCase(renameConversation.pending, (state) => {
        state.error = null
      })
      .addCase(renameConversation.fulfilled, (state, action) => {
        const index = state.items.findIndex((conv) => conv.id === action.payload.id)
        if (index !== -1) {
          state.items[index] = action.payload
        }
      })
      .addCase(renameConversation.rejected, (state, action) => {
        state.error = action.payload ?? '重命名对话失败'
      })

    // Delete conversation
    builder
      .addCase(deleteConversation.pending, (state) => {
        state.error = null
      })
      .addCase(deleteConversation.fulfilled, (state, action) => {
        state.items = state.items.filter((conv) => conv.id !== action.payload)
        state.total -= 1
        if (state.currentId === action.payload) {
          state.currentId = null
        }
      })
      .addCase(deleteConversation.rejected, (state, action) => {
        state.error = action.payload ?? '删除对话失败'
      })
  },
})

export const {
  setCurrentConversation,
  clearError,
  clearConversations,
  updateConversationTitle,
} = conversationsSlice.actions

export default conversationsSlice.reducer