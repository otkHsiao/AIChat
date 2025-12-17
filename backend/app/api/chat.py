"""Chat API routes for sending messages and streaming responses."""

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.core.dependencies import CurrentUserId, CosmosDB
from app.schemas.message import (
    ChatRequest,
    ChatResponse,
    MessageListResponse,
    MessageResponse,
)
from app.services.azure_openai import get_openai_service
from app.services.blob_storage import get_blob_service

router = APIRouter()


@router.get("/conversations/{conversation_id}/messages", response_model=dict)
async def get_messages(
    conversation_id: str,
    user_id: CurrentUserId,
    db: CosmosDB,
    limit: int = Query(default=50, ge=1, le=200),
    before: Optional[str] = Query(default=None, description="获取此消息ID之前的消息"),
) -> dict:
    """
    Get message history for a conversation.
    """
    # Verify conversation belongs to user
    conversation = await db.get_conversation(conversation_id, user_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    messages = await db.get_messages_by_conversation(
        conversation_id=conversation_id,
        limit=limit + 1,  # Fetch one extra to check if there are more
        before_id=before,
    )

    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]

    return {
        "success": True,
        "data": MessageListResponse(
            messages=[MessageResponse(**msg) for msg in messages],
            hasMore=has_more,
        ),
    }


@router.post("/conversations/{conversation_id}/messages", response_model=dict)
async def send_message(
    conversation_id: str,
    chat_request: ChatRequest,
    user_id: CurrentUserId,
    db: CosmosDB,
) -> dict:
    """
    Send a message and get a non-streaming response.
    """
    # Verify conversation belongs to user
    conversation = await db.get_conversation(conversation_id, user_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    # Get message history for context
    history = await db.get_messages_by_conversation(conversation_id, limit=20)

    # Process attachments
    attachments = []
    if chat_request.attachments:
        blob_service = get_blob_service()
        for att in chat_request.attachments:
            # Get fresh URL for the attachment
            # In a real implementation, you'd look up the blob name from a database
            attachments.append({
                "type": att.type,
                "url": f"placeholder-url-for-{att.id}",  # Would be fetched from storage
            })

    # Save user message
    user_message = await db.create_message(
        conversation_id=conversation_id,
        message_data={
            "role": "user",
            "content": chat_request.content,
            "attachments": [att.model_dump() for att in (chat_request.attachments or [])],
        },
    )

    # Get AI response
    openai_service = get_openai_service()
    history_for_api = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in history
        if msg["role"] in ("user", "assistant")
    ]

    response = await openai_service.chat_completion(
        system_prompt=conversation["systemPrompt"],
        history=history_for_api,
        user_message=chat_request.content,
        attachments=attachments if attachments else None,
    )

    # Save assistant message
    assistant_message = await db.create_message(
        conversation_id=conversation_id,
        message_data={
            "role": "assistant",
            "content": response["content"],
            "tokens": response["tokens"],
        },
    )

    # Update conversation message count
    await db.update_conversation(
        conversation_id,
        user_id,
        {"messageCount": conversation["messageCount"] + 2},
    )

    return {
        "success": True,
        "data": ChatResponse(
            userMessage=MessageResponse(**user_message),
            assistantMessage=MessageResponse(**assistant_message),
        ),
    }


@router.post("/conversations/{conversation_id}/messages/stream")
async def send_message_stream(
    conversation_id: str,
    chat_request: ChatRequest,
    user_id: CurrentUserId,
    db: CosmosDB,
) -> StreamingResponse:
    """
    Send a message and get a streaming response via SSE.
    """
    # Verify conversation belongs to user
    conversation = await db.get_conversation(conversation_id, user_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    # Get message history for context
    history = await db.get_messages_by_conversation(conversation_id, limit=20)

    # Save user message first
    user_message = await db.create_message(
        conversation_id=conversation_id,
        message_data={
            "role": "user",
            "content": chat_request.content,
            "attachments": [att.model_dump() for att in (chat_request.attachments or [])],
        },
    )

    async def generate():
        """Generate SSE events for streaming response."""
        openai_service = get_openai_service()
        
        history_for_api = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
            if msg["role"] in ("user", "assistant")
        ]

        # Send message start event
        message_id = None
        yield f"event: message_start\ndata: {json.dumps({'userMessageId': user_message['id']})}\n\n"

        full_content = ""
        tokens = {"input": 0, "output": 0}

        try:
            async for chunk in openai_service.chat_completion_stream(
                system_prompt=conversation["systemPrompt"],
                history=history_for_api,
                user_message=chat_request.content,
            ):
                if chunk["type"] == "content_delta":
                    full_content += chunk["delta"]
                    yield f"event: content_delta\ndata: {json.dumps({'delta': chunk['delta']})}\n\n"

                elif chunk["type"] == "finish":
                    # Save assistant message
                    assistant_message = await db.create_message(
                        conversation_id=conversation_id,
                        message_data={
                            "role": "assistant",
                            "content": full_content,
                            "tokens": tokens,
                        },
                    )
                    message_id = assistant_message["id"]

                    # Update conversation
                    await db.update_conversation(
                        conversation_id,
                        user_id,
                        {"messageCount": conversation["messageCount"] + 2},
                    )

                    yield f"event: message_end\ndata: {json.dumps({'messageId': message_id, 'tokens': tokens})}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )