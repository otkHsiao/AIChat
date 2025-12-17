import { useEffect } from 'react'
import { useParams } from 'react-router-dom'

import { useAppDispatch, useAppSelector } from '../store'
import { setCurrentConversation } from '../features/conversations/conversationsSlice'
import { ChatContainer } from '../components/Chat'

export default function ChatPage() {
  const dispatch = useAppDispatch()
  const { conversationId } = useParams<{ conversationId?: string }>()
  const currentId = useAppSelector((state) => state.conversations.currentId)

  useEffect(() => {
    if (conversationId && conversationId !== currentId) {
      dispatch(setCurrentConversation(conversationId))
    }
  }, [conversationId, currentId, dispatch])

  return <ChatContainer />
}