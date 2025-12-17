"""Common schemas used across the application."""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail schema."""

    code: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    success: bool = False
    error: ErrorDetail


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response schema."""

    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int
    limit: int
    offset: int
    has_more: bool