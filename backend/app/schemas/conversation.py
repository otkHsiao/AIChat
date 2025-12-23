"""Conversation related schemas."""

# List: 列表类型注解
# Optional: 可选类型注解
from typing import List, Optional

# BaseModel: Pydantic 的数据模型基类
# Field: 字段声明器，用于定义字段的验证规则（如最大长度、默认值）
from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""

    title: Optional[str] = Field(default="新对话", max_length=200)
    systemPrompt: Optional[str] = Field(
        default="你是一个有帮助的 AI 助手。",
        max_length=4000,
    )
    model: Optional[str] = Field(default="gpt-4o")


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""

    title: Optional[str] = Field(default=None, max_length=200)
    systemPrompt: Optional[str] = Field(default=None, max_length=4000)
    model: Optional[str] = None


class ConversationResponse(BaseModel):
    """Schema for conversation data in responses."""

    id: str
    userId: str
    title: str
    systemPrompt: str
    model: str
    messageCount: int
    createdAt: str
    updatedAt: str

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Schema for paginated conversation list response."""

    conversations: List[ConversationResponse]
    total: int
    limit: int
    offset: int


class ConversationDeleteResponse(BaseModel):
    """Schema for conversation deletion response."""

    success: bool = True
    message: str = "会话已删除"