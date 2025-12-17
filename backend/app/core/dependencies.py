"""FastAPI dependency injection utilities."""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import verify_token
from app.services.cosmos_db import CosmosDBService

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    """
    Dependency to extract and validate the current user ID from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials from request header
    
    Returns:
        The user ID from the validated token
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    user_id = verify_token(token, token_type="access")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


async def get_optional_user_id(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(HTTPBearer(auto_error=False))],
) -> Optional[str]:
    """
    Optional dependency to extract user ID if token is provided.
    
    Args:
        credentials: Optional HTTP Bearer credentials
    
    Returns:
        The user ID if token is valid, None otherwise
    """
    if credentials is None:
        return None
    
    return verify_token(credentials.credentials, token_type="access")


# Type aliases for cleaner dependency injection
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
OptionalUserId = Annotated[Optional[str], Depends(get_optional_user_id)]


# Database service dependency
_cosmos_service: Optional[CosmosDBService] = None


async def get_cosmos_db() -> CosmosDBService:
    """
    Dependency to get the Cosmos DB service instance.
    
    Returns:
        Initialized CosmosDBService instance
    """
    global _cosmos_service
    
    if _cosmos_service is None:
        _cosmos_service = CosmosDBService()
        await _cosmos_service.initialize()
    
    return _cosmos_service


CosmosDB = Annotated[CosmosDBService, Depends(get_cosmos_db)]