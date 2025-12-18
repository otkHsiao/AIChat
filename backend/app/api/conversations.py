"""Conversation management API routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.dependencies import CurrentUserId, CosmosDB
from app.core.sanitizer import sanitize_conversation_title
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDeleteResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("", response_model=dict)
@limiter.limit("60/minute")
async def list_conversations(
    request: Request,
    user_id: CurrentUserId,
    db: CosmosDB,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict:
    """
    Get all conversations for the current user.
    
    Returns paginated list of conversations sorted by updatedAt descending.
    """
    conversations = await db.get_conversations_by_user(
        user_id=user_id,
        limit=limit,
        offset=offset,
    )

    total = await db.count_conversations_by_user(user_id)

    return {
        "success": True,
        "data": ConversationListResponse(
            conversations=[
                ConversationResponse(**conv) for conv in conversations
            ],
            total=total,
            limit=limit,
            offset=offset,
        ),
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_conversation(
    request: Request,
    conversation_data: ConversationCreate,
    user_id: CurrentUserId,
    db: CosmosDB,
) -> dict:
    """
    Create a new conversation.
    """
    # Sanitize input
    sanitized_data = conversation_data.model_dump()
    if sanitized_data.get("title"):
        sanitized_data["title"] = sanitize_conversation_title(sanitized_data["title"])
    
    conversation = await db.create_conversation(
        user_id=user_id,
        conversation_data=sanitized_data,
    )

    return {
        "success": True,
        "data": ConversationResponse(**conversation),
    }


@router.get("/{conversation_id}", response_model=dict)
async def get_conversation(
    conversation_id: str,
    user_id: CurrentUserId,
    db: CosmosDB,
) -> dict:
    """
    Get a specific conversation by ID.
    """
    conversation = await db.get_conversation(conversation_id, user_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    return {
        "success": True,
        "data": ConversationResponse(**conversation),
    }


@router.put("/{conversation_id}", response_model=dict)
async def update_conversation(
    conversation_id: str,
    conversation_data: ConversationUpdate,
    user_id: CurrentUserId,
    db: CosmosDB,
) -> dict:
    """
    Update a conversation's title or system prompt.
    """
    # Check if conversation exists
    existing = await db.get_conversation(conversation_id, user_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    # Update conversation
    updates = conversation_data.model_dump(exclude_none=True)
    conversation = await db.update_conversation(conversation_id, user_id, updates)

    return {
        "success": True,
        "data": ConversationResponse(**conversation),
    }


@router.delete("/{conversation_id}", response_model=ConversationDeleteResponse)
async def delete_conversation(
    conversation_id: str,
    user_id: CurrentUserId,
    db: CosmosDB,
) -> ConversationDeleteResponse:
    """
    Delete a conversation and all its messages.
    """
    success = await db.delete_conversation(conversation_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    return ConversationDeleteResponse()