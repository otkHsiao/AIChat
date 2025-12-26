"""Pydantic schemas for request/response validation."""

from app.schemas.auth import (
    PasswordChange,
    TokenPayload,
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserInDB,
    UserLogin,
    UserResponse,
    UserSettings,
    UserSettingsUpdate,
)
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDeleteResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
)
from app.schemas.message import (
    Attachment,
    AttachmentRef,
    ChatRequest,
    ChatResponse,
    MessageCreate,
    MessageListResponse,
    MessageResponse,
    StreamEvent,
    TokenUsage,
)
from app.schemas.file import (
    FileDeleteResponse,
    FileInfoResponse,
    FileUploadResponse,
)
from app.schemas.common import (
    ErrorDetail,
    ErrorResponse,
    PaginationInfo,
    SuccessResponse,
)

__all__ = [
    # Auth
    "PasswordChange",
    "TokenPayload",
    "TokenRefresh",
    "TokenResponse",
    "UserCreate",
    "UserInDB",
    "UserLogin",
    "UserResponse",
    "UserSettings",
    "UserSettingsUpdate",
    # Conversation
    "ConversationCreate",
    "ConversationDeleteResponse",
    "ConversationListResponse",
    "ConversationResponse",
    "ConversationUpdate",
    # Message
    "Attachment",
    "AttachmentRef",
    "ChatRequest",
    "ChatResponse",
    "MessageCreate",
    "MessageListResponse",
    "MessageResponse",
    "StreamEvent",
    "TokenUsage",
    # File
    "FileDeleteResponse",
    "FileInfoResponse",
    "FileUploadResponse",
    # Common
    "ErrorDetail",
    "ErrorResponse",
    "PaginationInfo",
    "SuccessResponse",
]