"""File upload related schemas."""

# Literal: 字面量类型注解，限制值只能是指定的字符串之一
from typing import Literal

# BaseModel: Pydantic 的数据模型基类
from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    """Schema for file upload response."""

    id: str
    fileName: str
    type: Literal["image", "file"]
    mimeType: str
    size: int
    url: str
    createdAt: str


class FileInfoResponse(BaseModel):
    """Schema for file information response."""

    id: str
    fileName: str
    type: Literal["image", "file"]
    mimeType: str
    size: int
    url: str
    createdAt: str


class FileDeleteResponse(BaseModel):
    """Schema for file deletion response."""

    success: bool = True
    message: str = "文件已删除"