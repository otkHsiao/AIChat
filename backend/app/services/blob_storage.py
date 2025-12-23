"""
Azure Blob Storage 服务模块 - 文件存储操作。

本模块封装了与 Azure Blob Storage 的所有交互，提供：
1. 文件上传 - 将用户文件保存到云存储
2. 文件下载 - 获取存储的文件内容
3. 文件验证 - 检查文件类型和大小
4. SAS URL 生成 - 创建临时访问链接

Azure Blob Storage 概念：
- Storage Account: 存储账户，所有存储服务的顶层容器
- Container: 容器，类似于文件系统中的文件夹
- Blob: 二进制大对象，即存储的文件

存储路径设计：
文件保存路径格式：{user_id}/{file_id}{extension}
例如：a1b2c3d4-e5f6-7890/f9e8d7c6-b5a4-3210.png

这种设计的优点：
- 按用户隔离文件，便于管理和清理
- 使用 UUID 作为文件名，避免冲突和猜测
- 保留原始扩展名，方便识别文件类型

安全策略：
- 容器访问级别设为 Private
- 通过 SAS Token 提供临时访问权限
- SAS Token 有过期时间（默认 24 小时）
- 只允许上传白名单中的文件类型
"""

# datetime: 日期时间类，用于处理时间戳
# timedelta: 时间差类，用于计算 SAS Token 过期时间
# timezone: 时区类，用于 UTC 时间处理
from datetime import datetime, timedelta, timezone

# Any: 任意类型注解
# Dict: 字典类型注解
# Optional: 可选类型注解
from typing import Any, Dict, Optional

# uuid: Python 标准库，用于生成唯一的文件 ID
import uuid

# mimetypes: Python 标准库，用于根据 MIME 类型推断文件扩展名
import mimetypes

# BlobServiceClient: Azure Blob Storage 服务客户端
# BlobSasPermissions: SAS Token 权限配置类
# generate_blob_sas: 生成 Blob 级别 SAS Token 的函数
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas

# get_settings: 获取应用配置的函数
from app.core.config import get_settings


# ============================================================================
# 允许的文件类型配置
# ============================================================================

# 允许的图片类型（支持 GPT-4o Vision）
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}

# 允许的文档类型（可以提取文本内容）
ALLOWED_FILE_TYPES = {
    "application/pdf",                                                    # PDF 文档
    "text/plain",                                                         # 纯文本
    "text/markdown",                                                      # Markdown
    "application/msword",                                                 # Word .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # Word .docx
}

# 所有允许的类型（图片 + 文档）
ALL_ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_FILE_TYPES

# ============================================================================
# 文件扩展名到 MIME 类型的映射
# ============================================================================
# 当浏览器上传文件时 content_type 为 application/octet-stream 时
# 可以通过文件扩展名推断正确的 MIME 类型
EXTENSION_TO_MIME = {
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}

# ============================================================================
# 文件大小限制（字节）
# ============================================================================
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB - 图片上限
MAX_FILE_SIZE = 20 * 1024 * 1024   # 20 MB - 文档上限


class BlobStorageService:
    """
    Azure Blob Storage 服务类。
    
    封装所有文件存储操作，包括上传、下载、删除和 URL 生成。
    使用单例模式，通过 get_blob_service 函数获取实例。
    
    使用方式：
        blob_service = get_blob_service()
        result = await blob_service.upload_file(
            user_id="xxx",
            file_content=file_bytes,
            content_type="image/png",
            filename="photo.png"
        )
    """

    def __init__(self) -> None:
        """
        初始化 Blob Storage 服务。
        
        从连接字符串创建客户端，并获取容器引用。
        连接字符串包含存储账户名称和密钥。
        """
        self.settings = get_settings()
        
        # 从连接字符串创建 Blob 服务客户端
        # 连接字符串格式：
        # DefaultEndpointsProtocol=https;AccountName=xxx;AccountKey=xxx;EndpointSuffix=core.windows.net
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.settings.azure_storage_connection_string
        )
        
        # 保存容器名称
        self.container_name = self.settings.azure_storage_container_name
        
        # 获取容器客户端
        self.container_client = self.blob_service_client.get_container_client(
            self.container_name
        )

    def _get_file_type(self, mime_type: str) -> str:
        """
        根据 MIME 类型判断文件类别。
        
        将文件分为两类：
        - image: 图片文件，可用于 GPT-4o Vision
        - file: 文档文件，需要提取文本内容
        
        Args:
            mime_type: 文件的 MIME 类型
            
        Returns:
            str: "image" 或 "file"
        """
        if mime_type in ALLOWED_IMAGE_TYPES:
            return "image"
        return "file"

    def _get_mime_from_extension(self, filename: str) -> Optional[str]:
        """
        根据文件扩展名推断 MIME 类型。
        
        当浏览器上传文件时 content_type 为 application/octet-stream 时使用。
        
        Args:
            filename: 文件名（带扩展名）
            
        Returns:
            Optional[str]: MIME 类型，未知扩展名返回 None
        """
        import os
        # 提取扩展名并转小写
        _, ext = os.path.splitext(filename.lower())
        return EXTENSION_TO_MIME.get(ext)

    def validate_file(
        self, file_content: bytes, content_type: str, filename: str
    ) -> Dict[str, Any]:
        """
        验证上传的文件类型和大小。
        
        安全检查：
        1. 验证 MIME 类型在白名单中
        2. 验证文件大小不超过限制
        3. 处理 application/octet-stream 类型
        
        Args:
            file_content: 文件内容（字节）
            content_type: 客户端声明的 MIME 类型
            filename: 原始文件名
            
        Returns:
            Dict: 验证结果，包含：
                - type: 文件类别（"image" 或 "file"）
                - mime_type: 实际 MIME 类型
                - size: 文件大小（字节）
                - filename: 原始文件名
                
        Raises:
            ValueError: 如果文件类型不允许或大小超限
        """
        # 处理浏览器上传时 content_type 为 octet-stream 的情况
        actual_content_type = content_type
        if content_type == "application/octet-stream":
            # 尝试从扩展名推断 MIME 类型
            mime_from_ext = self._get_mime_from_extension(filename)
            if mime_from_ext:
                actual_content_type = mime_from_ext
        
        # 验证 MIME 类型在白名单中
        if actual_content_type not in ALL_ALLOWED_TYPES:
            raise ValueError(f"File type '{actual_content_type}' is not allowed")

        # 判断文件类别
        file_type = self._get_file_type(actual_content_type)

        # 验证文件大小
        file_size = len(file_content)
        max_size = MAX_IMAGE_SIZE if file_type == "image" else MAX_FILE_SIZE

        if file_size > max_size:
            max_mb = max_size // (1024 * 1024)
            raise ValueError(f"File size exceeds maximum allowed ({max_mb} MB)")

        return {
            "type": file_type,
            "mime_type": actual_content_type,
            "size": file_size,
            "filename": filename,
        }

    async def upload_file(
        self,
        user_id: str,
        file_content: bytes,
        content_type: str,
        filename: str,
    ) -> Dict[str, Any]:
        """
        上传文件到 Azure Blob Storage。
        
        完整的上传流程：
        1. 验证文件类型和大小
        2. 生成唯一的 Blob 名称
        3. 上传到存储
        4. 生成 SAS URL 供访问
        
        Args:
            user_id: 上传者的用户 ID（用于文件路径隔离）
            file_content: 文件内容（字节）
            content_type: 文件的 MIME 类型
            filename: 原始文件名（用于显示）
            
        Returns:
            Dict: 上传结果，包含：
                - id: 文件唯一 ID
                - fileName: 原始文件名
                - type: 文件类别（"image" 或 "file"）
                - mimeType: MIME 类型
                - size: 文件大小（字节）
                - blobName: Blob 存储路径
                - url: 带 SAS Token 的访问 URL
                - createdAt: 创建时间
                
        Raises:
            ValueError: 如果文件验证失败
        """
        # 验证文件类型和大小
        file_info = self.validate_file(file_content, content_type, filename)

        # 生成唯一的 Blob 名称
        # 格式：{user_id}/{file_id}{extension}
        file_id = str(uuid.uuid4())
        extension = mimetypes.guess_extension(content_type) or ""
        blob_name = f"{user_id}/{file_id}{extension}"

        # 获取 Blob 客户端并上传
        blob_client = self.container_client.get_blob_client(blob_name)
        blob_client.upload_blob(
            file_content,
            content_type=content_type,  # 设置 Content-Type，方便浏览器识别
            overwrite=True,              # 覆盖已存在的文件（理论上 UUID 不会冲突）
        )

        # 生成带 SAS Token 的访问 URL
        sas_url = self._generate_sas_url(blob_name)

        # 返回上传结果
        return {
            "id": file_id,
            "fileName": filename,
            "type": file_info["type"],
            "mimeType": content_type,
            "size": file_info["size"],
            "blobName": blob_name,       # 保存 Blob 名称，用于后续操作
            "url": sas_url,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_sas_url(
        self, blob_name: str, expiry_hours: int = 24
    ) -> str:
        """
        生成 Blob 的 SAS（共享访问签名）URL。
        
        SAS URL 允许临时访问私有 Blob，无需账户密钥。
        URL 包含签名和过期时间，过期后自动失效。
        
        SAS Token 参数说明：
        - sv: 服务版本
        - se: 过期时间
        - sr: 资源类型（b=blob）
        - sp: 权限（r=read）
        - sig: 签名
        
        Args:
            blob_name: Blob 的完整路径名称
            expiry_hours: SAS Token 的有效时间（小时，默认 24）
            
        Returns:
            str: 完整的带 SAS Token 的 URL
            
        URL 格式：
        https://{account}.blob.core.windows.net/{container}/{blob}?{sas_token}
        """
        # 从连接字符串解析账户信息
        # 连接字符串格式：key1=value1;key2=value2;...
        conn_str_parts = dict(
            part.split("=", 1)
            for part in self.settings.azure_storage_connection_string.split(";")
            if "=" in part
        )
        account_name = conn_str_parts.get("AccountName", "")
        account_key = conn_str_parts.get("AccountKey", "")

        # 生成 SAS Token
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=self.container_name,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),  # 只允许读取
            expiry=datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
        )

        # 构建完整 URL
        return f"https://{account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"

    async def get_file_url(self, blob_name: str) -> str:
        """
        获取现有 Blob 的新 SAS URL。
        
        当 SAS Token 过期或即将过期时，调用此方法获取新的访问 URL。
        
        Args:
            blob_name: Blob 的完整路径名称
            
        Returns:
            str: 新的带 SAS Token 的 URL
        """
        return self._generate_sas_url(blob_name)

    async def delete_file(self, blob_name: str) -> bool:
        """
        从 Blob Storage 删除文件。
        
        Args:
            blob_name: 要删除的 Blob 名称
            
        Returns:
            bool: 删除成功返回 True，失败返回 False
            
        Note:
            失败时不抛出异常，只返回 False
            调用者需要根据返回值决定后续处理
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            return True
        except Exception:
            # 可能的失败原因：Blob 不存在、权限不足等
            return False

    async def file_exists(self, blob_name: str) -> bool:
        """
        检查 Blob 是否存在。
        
        Args:
            blob_name: Blob 的完整路径名称
            
        Returns:
            bool: 存在返回 True，否则返回 False
        """
        blob_client = self.container_client.get_blob_client(blob_name)
        return blob_client.exists()

    async def download_file_content(self, url: str) -> Optional[bytes]:
        """
        下载文件内容。
        
        支持两种输入格式：
        1. 完整的 SAS URL
        2. Blob 名称（路径）
        
        如果输入是 SAS URL，会自动提取 Blob 名称。
        
        Args:
            url: SAS URL 或 Blob 名称
            
        Returns:
            Optional[bytes]: 文件内容（字节），失败返回 None
        """
        try:
            # 从 SAS URL 提取 Blob 名称
            blob_name = url
            if "blob.core.windows.net" in url:
                # 解析 URL 获取 Blob 名称
                # URL 格式: https://<account>.blob.core.windows.net/<container>/<blob_name>?<sas>
                from urllib.parse import urlparse, unquote
                parsed = urlparse(url)
                path_parts = parsed.path.split("/")
                # path_parts[0] 是空字符串，[1] 是容器名，后面是 Blob 路径
                if len(path_parts) >= 3:
                    blob_name = "/".join(path_parts[2:])
                    blob_name = unquote(blob_name)  # URL 解码
            
            # 下载 Blob 内容
            blob_client = self.container_client.get_blob_client(blob_name)
            download = blob_client.download_blob()
            return download.readall()
        except Exception as e:
            print(f"Error downloading file: {e}")
            return None

    async def download_text_file(self, url: str) -> Optional[str]:
        """
        下载并解码文本文件内容。
        
        自动处理编码：
        1. 首先尝试 UTF-8
        2. 失败则尝试 GBK（中文编码）
        3. 最后使用 UTF-8 忽略错误
        
        Args:
            url: SAS URL 或 Blob 名称
            
        Returns:
            Optional[str]: 解码后的文本内容，失败返回 None
            
        适用场景：
        - 读取 Markdown 文件内容用于 AI 分析
        - 读取纯文本文件
        """
        content = await self.download_file_content(url)
        if content:
            try:
                # 首选 UTF-8 编码
                return content.decode("utf-8")
            except UnicodeDecodeError:
                # 尝试 GBK（常见于中文 Windows 系统）
                try:
                    return content.decode("gbk")
                except:
                    # 最后使用 UTF-8 忽略无法解码的字符
                    return content.decode("utf-8", errors="ignore")
        return None


# ============================================================================
# 单例模式实现
# ============================================================================

# 全局服务实例
_blob_service: Optional[BlobStorageService] = None


def get_blob_service() -> BlobStorageService:
    """
    获取 Blob Storage 服务的单例实例。
    
    使用单例模式确保：
    1. 整个应用共享同一个服务实例
    2. 只创建一次客户端连接
    3. 避免重复建立连接
    
    Returns:
        BlobStorageService: 服务实例
        
    使用方式：
        from app.services.blob_storage import get_blob_service
        
        blob_service = get_blob_service()
        result = await blob_service.upload_file(...)
    """
    global _blob_service
    
    if _blob_service is None:
        _blob_service = BlobStorageService()
    
    return _blob_service