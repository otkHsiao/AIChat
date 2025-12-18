"""Message related schemas."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class Attachment(BaseModel):
    """Schema for message attachment."""

    id: str
    type: Literal["image", "file"]
    fileName: Optional[str] = None
    url: Optional[str] = None
    mimeType: Optional[str] = None
    size: Optional[int] = None


class AttachmentRef(BaseModel):
    """Schema for referencing an uploaded attachment in message creation."""

    id: str
    type: Literal["image", "file"]
    url: Optional[str] = None
    fileName: Optional[str] = None
    mimeType: Optional[str] = None


class TokenUsage(BaseModel):
    """Schema for token usage information."""

    input: int
    output: int


class MessageCreate(BaseModel):
    """Schema for creating a new message."""

    content: str = Field(..., min_length=1, max_length=32000)
    attachments: Optional[List[AttachmentRef]] = None


class MessageResponse(BaseModel):
    """Schema for message data in responses."""

    id: str
    conversationId: str
    role: Literal["user", "assistant", "system"]
    content: str
    attachments: Optional[List[Attachment]] = None
    tokens: Optional[TokenUsage] = None
    createdAt: str

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Schema for paginated message list response."""

    messages: List[MessageResponse]
    hasMore: bool


class ChatRequest(BaseModel):
    """Schema for chat completion request."""

    content: str = Field(..., min_length=1, max_length=32000)
    attachments: Optional[List[AttachmentRef]] = None


class ChatResponse(BaseModel):
    """Schema for non-streaming chat response."""

    userMessage: MessageResponse
    assistantMessage: MessageResponse


class StreamEvent(BaseModel):
    """Schema for SSE stream event."""

    event: str
    data: dict