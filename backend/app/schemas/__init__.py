"""Pydantic schemas for request/response validation."""

from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    TokenRefresh,
)
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationListResponse,
)
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
    MessageListResponse,
    Attachment,
)
from app.schemas.file import (
    FileUploadResponse,
    FileInfoResponse,
)
from app.schemas.common import (
    SuccessResponse,
    ErrorResponse,
    ErrorDetail,
)

__all__ = [
    # Auth
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "TokenRefresh",
    # Conversation
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "ConversationListResponse",
    # Message
    "MessageCreate",
    "MessageResponse",
    "MessageListResponse",
    "Attachment",
    # File
    "FileUploadResponse",
    "FileInfoResponse",
    # Common
    "SuccessResponse",
    "ErrorResponse",
    "ErrorDetail",
]