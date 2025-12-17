"""Azure Blob Storage service for file operations."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import uuid
import mimetypes

from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas

from app.core.config import get_settings


# Allowed file types
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_FILE_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALL_ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_FILE_TYPES

# Size limits (in bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_FILE_SIZE = 20 * 1024 * 1024   # 20 MB


class BlobStorageService:
    """Service class for Azure Blob Storage operations."""

    def __init__(self) -> None:
        """Initialize the Blob Storage service."""
        self.settings = get_settings()
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.settings.azure_storage_connection_string
        )
        self.container_name = self.settings.azure_storage_container_name
        self.container_client = self.blob_service_client.get_container_client(
            self.container_name
        )

    def _get_file_type(self, mime_type: str) -> str:
        """Determine if file is an image or document."""
        if mime_type in ALLOWED_IMAGE_TYPES:
            return "image"
        return "file"

    def validate_file(
        self, file_content: bytes, content_type: str, filename: str
    ) -> Dict[str, Any]:
        """
        Validate uploaded file type and size.
        
        Args:
            file_content: The file content as bytes
            content_type: MIME type of the file
            filename: Original filename
        
        Returns:
            Dict with validation result and file info
        
        Raises:
            ValueError: If file type or size is invalid
        """
        # Check MIME type
        if content_type not in ALL_ALLOWED_TYPES:
            raise ValueError(f"File type '{content_type}' is not allowed")

        # Determine file type
        file_type = self._get_file_type(content_type)

        # Check size
        file_size = len(file_content)
        max_size = MAX_IMAGE_SIZE if file_type == "image" else MAX_FILE_SIZE

        if file_size > max_size:
            max_mb = max_size // (1024 * 1024)
            raise ValueError(f"File size exceeds maximum allowed ({max_mb} MB)")

        return {
            "type": file_type,
            "mime_type": content_type,
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
        Upload a file to Azure Blob Storage.
        
        Args:
            user_id: ID of the user uploading the file
            file_content: The file content as bytes
            content_type: MIME type of the file
            filename: Original filename
        
        Returns:
            Dict containing file metadata and URL
        """
        # Validate file
        file_info = self.validate_file(file_content, content_type, filename)

        # Generate unique blob name
        file_id = str(uuid.uuid4())
        extension = mimetypes.guess_extension(content_type) or ""
        blob_name = f"{user_id}/{file_id}{extension}"

        # Upload to blob storage
        blob_client = self.container_client.get_blob_client(blob_name)
        blob_client.upload_blob(
            file_content,
            content_type=content_type,
            overwrite=True,
        )

        # Generate SAS URL
        sas_url = self._generate_sas_url(blob_name)

        return {
            "id": file_id,
            "fileName": filename,
            "type": file_info["type"],
            "mimeType": content_type,
            "size": file_info["size"],
            "blobName": blob_name,
            "url": sas_url,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_sas_url(
        self, blob_name: str, expiry_hours: int = 24
    ) -> str:
        """
        Generate a SAS URL for accessing a blob.
        
        Args:
            blob_name: Name of the blob
            expiry_hours: Hours until the SAS token expires
        
        Returns:
            Full URL with SAS token
        """
        # Parse connection string to get account details
        conn_str_parts = dict(
            part.split("=", 1)
            for part in self.settings.azure_storage_connection_string.split(";")
            if "=" in part
        )
        account_name = conn_str_parts.get("AccountName", "")
        account_key = conn_str_parts.get("AccountKey", "")

        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=self.container_name,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
        )

        return f"https://{account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"

    async def get_file_url(self, blob_name: str) -> str:
        """Get a fresh SAS URL for an existing blob."""
        return self._generate_sas_url(blob_name)

    async def delete_file(self, blob_name: str) -> bool:
        """
        Delete a file from Blob Storage.
        
        Args:
            blob_name: Name of the blob to delete
        
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            return True
        except Exception:
            return False

    async def file_exists(self, blob_name: str) -> bool:
        """Check if a blob exists."""
        blob_client = self.container_client.get_blob_client(blob_name)
        return blob_client.exists()


# Singleton instance
_blob_service: Optional[BlobStorageService] = None


def get_blob_service() -> BlobStorageService:
    """Get or create the Blob Storage service instance."""
    global _blob_service
    
    if _blob_service is None:
        _blob_service = BlobStorageService()
    
    return _blob_service