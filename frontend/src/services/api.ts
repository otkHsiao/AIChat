import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import type { RootState } from '../store'
import type {
  User,
  AuthResponse,
  LoginCredentials,
  RegisterData,
  Conversation,
  ConversationCreate,
  ConversationUpdate,
  Message,
  FileUpload,
  PaginatedResponse,
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// Backend response wrapper type
interface ApiResponse<T> {
  success: boolean
  data: T
}

// Backend conversation list response
interface ConversationListData {
  conversations: Conversation[]
  total: number
  limit: number
  offset: number
}

// Backend message list response
interface MessageListData {
  messages: Message[]
  hasMore: boolean
}

/**
 * RTK Query base API configuration
 */
export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: API_BASE_URL,
    prepareHeaders: (headers, { getState }) => {
      // Get token from auth state
      const token = (getState() as RootState).auth.token
      if (token) {
        headers.set('Authorization', `Bearer ${token}`)
      }
      return headers
    },
  }),
  tagTypes: ['User', 'Conversation', 'Message', 'File'],
  endpoints: (builder) => ({
    // ============ Auth Endpoints ============
    login: builder.mutation<AuthResponse, LoginCredentials>({
      query: (credentials) => ({
        url: '/auth/login',
        method: 'POST',
        body: credentials,
      }),
    }),

    register: builder.mutation<AuthResponse, RegisterData>({
      query: (data) => ({
        url: '/auth/register',
        method: 'POST',
        body: data,
      }),
    }),

    refreshToken: builder.mutation<AuthResponse, { refreshToken: string }>({
      query: (data) => ({
        url: '/auth/refresh',
        method: 'POST',
        body: data,
      }),
    }),

    getCurrentUser: builder.query<User, void>({
      query: () => '/auth/me',
      transformResponse: (response: ApiResponse<User>) => response.data,
      providesTags: ['User'],
    }),

    // ============ Conversation Endpoints ============
    getConversations: builder.query<
      PaginatedResponse<Conversation>,
      { limit?: number; offset?: number }
    >({
      query: ({ limit = 50, offset = 0 }) =>
        `/conversations?limit=${limit}&offset=${offset}`,
      transformResponse: (response: ApiResponse<ConversationListData>) => ({
        items: response.data.conversations,
        total: response.data.total,
        limit: response.data.limit,
        offset: response.data.offset,
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.items.map(({ id }) => ({
                type: 'Conversation' as const,
                id,
              })),
              { type: 'Conversation', id: 'LIST' },
            ]
          : [{ type: 'Conversation', id: 'LIST' }],
    }),

    getConversation: builder.query<Conversation, string>({
      query: (id) => `/conversations/${id}`,
      transformResponse: (response: ApiResponse<Conversation>) => response.data,
      providesTags: (_result, _error, id) => [{ type: 'Conversation', id }],
    }),

    createConversation: builder.mutation<Conversation, ConversationCreate>({
      query: (data) => ({
        url: '/conversations',
        method: 'POST',
        body: data,
      }),
      transformResponse: (response: ApiResponse<Conversation>) => response.data,
      invalidatesTags: [{ type: 'Conversation', id: 'LIST' }],
    }),

    updateConversation: builder.mutation<
      Conversation,
      { id: string; data: ConversationUpdate }
    >({
      query: ({ id, data }) => ({
        url: `/conversations/${id}`,
        method: 'PUT',
        body: data,
      }),
      transformResponse: (response: ApiResponse<Conversation>) => response.data,
      invalidatesTags: (_result, _error, { id }) => [
        { type: 'Conversation', id },
        { type: 'Conversation', id: 'LIST' },
      ],
    }),

    deleteConversation: builder.mutation<void, string>({
      query: (id) => ({
        url: `/conversations/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, id) => [
        { type: 'Conversation', id },
        { type: 'Conversation', id: 'LIST' },
      ],
    }),

    // ============ Message Endpoints ============
    getMessages: builder.query<
      PaginatedResponse<Message>,
      { conversationId: string; limit?: number; before?: string }
    >({
      query: ({ conversationId, limit = 50, before }) => {
        let url = `/conversations/${conversationId}/messages?limit=${limit}`
        if (before) {
          url += `&before=${before}`
        }
        return url
      },
      transformResponse: (response: ApiResponse<MessageListData>, _meta, arg) => ({
        items: response.data.messages,
        total: response.data.messages.length,
        limit: arg.limit || 50,
        offset: 0,
        hasMore: response.data.hasMore,
      }),
      providesTags: (result, _error, { conversationId }) =>
        result
          ? [
              ...result.items.map(({ id }) => ({
                type: 'Message' as const,
                id,
              })),
              { type: 'Message', id: conversationId },
            ]
          : [{ type: 'Message', id: conversationId }],
    }),

    // ============ File Endpoints ============
    uploadFile: builder.mutation<FileUpload, FormData>({
      query: (formData) => ({
        url: '/files/upload',
        method: 'POST',
        body: formData,
      }),
      transformResponse: (response: ApiResponse<FileUpload>) => response.data,
      invalidatesTags: ['File'],
    }),

    getFile: builder.query<FileUpload, string>({
      query: (id) => `/files/${id}`,
      transformResponse: (response: ApiResponse<FileUpload>) => response.data,
      providesTags: (_result, _error, id) => [{ type: 'File', id }],
    }),

    deleteFile: builder.mutation<void, string>({
      query: (id) => ({
        url: `/files/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, id) => [{ type: 'File', id }],
    }),
  }),
})

// Export hooks for usage in components
export const {
  // Auth
  useLoginMutation,
  useRegisterMutation,
  useRefreshTokenMutation,
  useGetCurrentUserQuery,
  // Conversations
  useGetConversationsQuery,
  useGetConversationQuery,
  useCreateConversationMutation,
  useUpdateConversationMutation,
  useDeleteConversationMutation,
  // Messages
  useGetMessagesQuery,
  // Files
  useUploadFileMutation,
  useGetFileQuery,
  useDeleteFileMutation,
} = api