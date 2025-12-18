"""File upload API routes."""

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.dependencies import CurrentUserId
from app.schemas.file import FileDeleteResponse, FileUploadResponse
from app.services.blob_storage import get_blob_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/upload", response_model=dict, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def upload_file(
    request: Request,
    user_id: CurrentUserId,
    file: UploadFile = File(...),
) -> dict:
    """
    Upload a file (image or document).
    
    Supported image formats: jpg, png, gif, webp (max 10MB)
    Supported document formats: pdf, txt, md, doc, docx (max 20MB)
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名不能为空",
        )

    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法确定文件类型",
        )

    # Read file content
    content = await file.read()

    # Upload to blob storage
    blob_service = get_blob_service()

    try:
        result = await blob_service.upload_file(
            user_id=user_id,
            file_content=content,
            content_type=file.content_type,
            filename=file.filename,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return {
        "success": True,
        "data": FileUploadResponse(
            id=result["id"],
            fileName=result["fileName"],
            type=result["type"],
            mimeType=result["mimeType"],
            size=result["size"],
            url=result["url"],
            createdAt=result["createdAt"],
        ),
    }


@router.get("/{file_id}", response_model=dict)
async def get_file_info(
    file_id: str,
    user_id: CurrentUserId,
) -> dict:
    """
    Get information about an uploaded file.
    
    Note: This is a simplified implementation. In production,
    you would store file metadata in the database.
    """
    # In a real implementation, you would:
    # 1. Look up file metadata in database
    # 2. Verify the file belongs to the user
    # 3. Generate a fresh SAS URL
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="文件信息查询功能待实现",
    )


@router.delete("/{file_id}", response_model=FileDeleteResponse)
async def delete_file(
    file_id: str,
    user_id: CurrentUserId,
) -> FileDeleteResponse:
    """
    Delete an uploaded file.
    
    Note: This is a simplified implementation. In production,
    you would store file metadata in the database.
    """
    # In a real implementation, you would:
    # 1. Look up file metadata in database
    # 2. Verify the file belongs to the user
    # 3. Delete from blob storage
    # 4. Delete metadata from database
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="文件删除功能待实现",
    )