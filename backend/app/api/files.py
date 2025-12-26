"""
文件上传 API 路由模块。

本模块处理文件上传相关的 HTTP 请求：
1. 上传文件 - 将图片或文档保存到 Azure Blob Storage
2. 获取文件信息 - 查询已上传文件的元数据（待实现）
3. 删除文件 - 从存储中删除文件（待实现）

支持的文件类型：

图片（用于 GPT-4o Vision 分析）：
- image/jpeg (.jpg, .jpeg)
- image/png (.png)
- image/gif (.gif)
- image/webp (.webp)
- 大小限制：10 MB

文档（提取文本内容）：
- application/pdf (.pdf)
- text/plain (.txt)
- text/markdown (.md)
- application/msword (.doc)
- application/vnd.openxmlformats-officedocument.wordprocessingml.document (.docx)
- 大小限制：20 MB

上传流程：
┌─────────────────────────────────────────────────────────────────────────┐
│                           文件上传流程                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐   POST /files/upload    ┌──────────┐                      │
│  │  前端     │ ─────────────────────> │  后端     │                      │
│  │          │  multipart/form-data   │          │                      │
│  │          │                         │          │                      │
│  │          │                         └─────┬────┘                      │
│  │          │                               │                            │
│  │          │                         ┌─────▼────────────┐              │
│  │          │                         │  Azure Blob      │              │
│  │          │                         │  Storage         │              │
│  │          │                         │                  │              │
│  │          │                         │  /{userId}/      │              │
│  │          │                         │  {fileId}.ext    │              │
│  │          │                         └─────┬────────────┘              │
│  │          │                               │                            │
│  │          │  <─────────────────────────────                           │
│  │          │  {id, fileName, url, ...}                                 │
│  └──────────┘                                                           │
│       │                                                                  │
│       │ 使用返回的 URL 发送给 AI                                          │
│       ▼                                                                  │
│  ┌─────────────────────────────────────┐                                │
│  │  在消息中引用文件 URL               │                                │
│  └─────────────────────────────────────┘                                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

速率限制：
- 上传：30 次/分钟
"""

# APIRouter: 创建路由器实例
# File: 文件参数声明器，用于定义文件上传参数
# HTTPException: HTTP 异常类，用于返回错误响应
# Request: HTTP 请求对象
# UploadFile: FastAPI 的文件上传类型，封装了上传文件的信息和内容
# status: HTTP 状态码常量集合
from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

# Limiter: 速率限制器类
from slowapi import Limiter

# get_remote_address: 获取客户端 IP 地址的工具函数
from slowapi.util import get_remote_address

# CurrentUserId: 当前认证用户 ID 的类型别名（依赖注入）
from app.core.dependencies import CurrentUserId

# FileDeleteResponse: 文件删除响应的数据模型
# FileUploadResponse: 文件上传响应的数据模型（包含文件 ID、URL 等）
from app.schemas.file import FileDeleteResponse, FileUploadResponse

# SuccessResponse: 标准成功响应的泛型模型
from app.schemas.common import SuccessResponse

# get_blob_service: 获取 Azure Blob Storage 服务的单例实例
from app.services.blob_storage import get_blob_service

# 创建路由器实例
# 这个路由器会被注册到 /api/files 路径下
router = APIRouter()

# 创建速率限制器
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# 上传文件
# ============================================================================

@router.post("/upload", response_model=SuccessResponse[FileUploadResponse], status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")  # 限制每分钟 30 次上传
async def upload_file(
    request: Request,
    user_id: CurrentUserId,
    file: UploadFile = File(...),  # 使用 FastAPI 的文件上传
) -> SuccessResponse[FileUploadResponse]:
    """
    上传文件（图片或文档）。
    
    接受 multipart/form-data 格式的文件上传请求。
    文件会被保存到 Azure Blob Storage，并返回带 SAS Token 的访问 URL。
    
    支持的格式：
    - 图片：jpg, png, gif, webp（最大 10MB）
    - 文档：pdf, txt, md, doc, docx（最大 20MB）
    
    返回的 URL 有效期为 24 小时，过期后需要重新获取。
    
    使用场景：
    1. 上传图片让 AI 分析
    2. 上传文档让 AI 阅读内容
    
    Args:
        request: FastAPI 请求对象（用于速率限制）
        user_id: 当前用户 ID（从令牌提取）
        file: 上传的文件（UploadFile 类型）
        
    Returns:
        SuccessResponse[FileUploadResponse]: 包含文件信息和访问 URL 的响应
            - id: 文件唯一 ID
            - fileName: 原始文件名
            - type: 文件类别（"image" 或 "file"）
            - mimeType: MIME 类型
            - size: 文件大小（字节）
            - url: 带 SAS Token 的访问 URL
            - createdAt: 上传时间
            
    Raises:
        HTTPException:
            - 400: 文件名为空、类型无法确定、类型不允许或大小超限
    """
    # 验证文件名
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名不能为空",
        )

    # 验证文件类型
    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法确定文件类型",
        )

    # 读取文件内容
    content = await file.read()

    # 上传到 Blob Storage
    blob_service = get_blob_service()

    try:
        # 验证并上传文件
        result = await blob_service.upload_file(
            user_id=user_id,
            file_content=content,
            content_type=file.content_type,
            filename=file.filename,
        )
    except ValueError as e:
        # 验证失败（类型不允许或大小超限）
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # 返回上传结果
    return SuccessResponse(
        data=FileUploadResponse(
            id=result["id"],
            fileName=result["fileName"],
            type=result["type"],
            mimeType=result["mimeType"],
            size=result["size"],
            url=result["url"],
            createdAt=result["createdAt"],
        )
    )


# ============================================================================
# 获取文件信息（待实现）
# ============================================================================

@router.get("/{file_id}", response_model=dict)
async def get_file_info(
    file_id: str,
    user_id: CurrentUserId,
) -> dict:
    """
    获取已上传文件的信息（待实现）。
    
    完整实现应该：
    1. 在数据库中查询文件元数据
    2. 验证文件属于当前用户
    3. 生成新的 SAS URL（如果原 URL 已过期）
    
    当前实现：返回 501 Not Implemented
    
    Args:
        file_id: 文件 ID（路径参数）
        user_id: 当前用户 ID
        
    Raises:
        HTTPException: 501 错误，功能未实现
        
    TODO:
        - 在数据库中存储文件元数据
        - 实现文件所有权验证
        - 实现 SAS URL 刷新
    """
    # 完整实现步骤：
    # 1. 在数据库中查询文件元数据
    # 2. 验证文件属于当前用户
    # 3. 生成新的 SAS URL
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="文件信息查询功能待实现",
    )


# ============================================================================
# 删除文件（待实现）
# ============================================================================

@router.delete("/{file_id}", response_model=FileDeleteResponse)
async def delete_file(
    file_id: str,
    user_id: CurrentUserId,
) -> FileDeleteResponse:
    """
    删除已上传的文件（待实现）。
    
    完整实现应该：
    1. 在数据库中查询文件元数据
    2. 验证文件属于当前用户
    3. 从 Blob Storage 删除文件
    4. 从数据库删除元数据
    
    当前实现：返回 501 Not Implemented
    
    Args:
        file_id: 文件 ID（路径参数）
        user_id: 当前用户 ID
        
    Raises:
        HTTPException: 501 错误，功能未实现
        
    TODO:
        - 在数据库中存储文件元数据
        - 实现级联删除（Blob + 数据库）
        - 处理删除失败的情况
    """
    # 完整实现步骤：
    # 1. 在数据库中查询文件元数据
    # 2. 验证文件属于当前用户
    # 3. 从 Blob Storage 删除文件
    # 4. 从数据库删除元数据
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="文件删除功能待实现",
    )