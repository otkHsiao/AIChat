"""Authentication API routes."""

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import CurrentUserId, CosmosDB
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.schemas.auth import (
    PasswordChange,
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserSettingsUpdate,
)

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: CosmosDB) -> TokenResponse:
    """
    Register a new user.
    
    Creates a new user account and returns authentication tokens.
    """
    # Check if email already exists
    existing_user = await db.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="该邮箱已被注册",
        )

    # Create user
    user = await db.create_user({
        "email": user_data.email,
        "username": user_data.username,
        "passwordHash": get_password_hash(user_data.password),
    })

    # Generate tokens
    access_token = create_access_token(subject=user["id"])
    refresh_token = create_refresh_token(subject=user["id"])

    return TokenResponse(
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            username=user["username"],
            createdAt=user["createdAt"],
            settings=user.get("settings"),
        ),
        accessToken=access_token,
        refreshToken=refresh_token,
        expiresIn=86400,
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: CosmosDB) -> TokenResponse:
    """
    Login with email and password.
    
    Returns authentication tokens if credentials are valid.
    """
    # Find user by email
    user = await db.get_user_by_email(credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    # Verify password
    if not verify_password(credentials.password, user["passwordHash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    # Generate tokens
    access_token = create_access_token(subject=user["id"])
    refresh_token = create_refresh_token(subject=user["id"])

    return TokenResponse(
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            username=user["username"],
            createdAt=user["createdAt"],
            settings=user.get("settings"),
        ),
        accessToken=access_token,
        refreshToken=refresh_token,
        expiresIn=86400,
    )


@router.post("/refresh", response_model=dict)
async def refresh_token(token_data: TokenRefresh) -> dict:
    """
    Refresh access token using refresh token.
    """
    user_id = verify_token(token_data.refreshToken, token_type="refresh")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或已过期的刷新令牌",
        )

    # Generate new access token
    access_token = create_access_token(subject=user_id)

    return {
        "success": True,
        "data": {
            "accessToken": access_token,
            "expiresIn": 86400,
        },
    }


@router.get("/me", response_model=dict)
async def get_current_user(user_id: CurrentUserId, db: CosmosDB) -> dict:
    """
    Get current authenticated user's information.
    """
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    return {
        "success": True,
        "data": UserResponse(
            id=user["id"],
            email=user["email"],
            username=user["username"],
            createdAt=user["createdAt"],
            settings=user.get("settings"),
        ),
    }


@router.put("/settings", response_model=dict)
async def update_settings(
    settings: UserSettingsUpdate,
    user_id: CurrentUserId,
    db: CosmosDB,
) -> dict:
    """
    Update current user's settings.
    """
    updates = {"settings": settings.model_dump(exclude_none=True)}
    user = await db.update_user(user_id, updates)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    return {
        "success": True,
        "data": user.get("settings"),
    }


@router.put("/password", response_model=dict)
async def change_password(
    password_data: PasswordChange,
    user_id: CurrentUserId,
    db: CosmosDB,
) -> dict:
    """
    Change current user's password.
    """
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    # Verify current password
    if not verify_password(password_data.currentPassword, user["passwordHash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="当前密码错误",
        )

    # Update password
    await db.update_user(user_id, {
        "passwordHash": get_password_hash(password_data.newPassword),
    })

    return {
        "success": True,
        "message": "密码已更新",
    }