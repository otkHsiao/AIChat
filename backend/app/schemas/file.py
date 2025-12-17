"""File upload related schemas."""

from typing import Literal

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