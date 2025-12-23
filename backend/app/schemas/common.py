"""Common schemas used across the application."""

# Any: 任意类型注解
# Generic: 泛型基类，用于创建泛型类型
# Optional: 可选类型注解
# TypeVar: 类型变量，用于定义泛型参数
from typing import Any, Generic, Optional, TypeVar

# BaseModel: Pydantic 的数据模型基类
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