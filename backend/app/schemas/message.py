"""Message related schemas."""

# List: 列表类型注解
# Literal: 字面量类型注解，限制值只能是指定的字符串之一（如 "user" | "assistant"）
# Optional: 可选类型注解
from typing import List, Literal, Optional

# BaseModel: Pydantic 的数据模型基类
# Field: 字段声明器，用于定义字段的验证规则
# model_validator: 模型级验证器装饰器，用于跨字段验证
from pydantic import BaseModel, Field, model_validator


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

    content: str = Field(default="", max_length=32000)
    attachments: Optional[List[AttachmentRef]] = None

    @model_validator(mode='after')
    def validate_content_or_attachments(self) -> 'MessageCreate':
        """Ensure at least content or attachments are provided."""
        if not self.content.strip() and (not self.attachments or len(self.attachments) == 0):
            raise ValueError('消息内容和附件不能同时为空')
        return self


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

    content: str = Field(default="", max_length=32000)
    attachments: Optional[List[AttachmentRef]] = None

    @model_validator(mode='after')
    def validate_content_or_attachments(self) -> 'ChatRequest':
        """Ensure at least content or attachments are provided."""
        if not self.content.strip() and (not self.attachments or len(self.attachments) == 0):
            raise ValueError('消息内容和附件不能同时为空')
        return self


class ChatResponse(BaseModel):
    """Schema for non-streaming chat response."""

    userMessage: MessageResponse
    assistantMessage: MessageResponse


class StreamEvent(BaseModel):
    """Schema for SSE stream event."""

    event: str
    data: dict