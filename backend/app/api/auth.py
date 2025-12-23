"""
认证 API 路由模块。

本模块处理所有与用户认证相关的 HTTP 请求：
1. 用户注册（当前已禁用）
2. 用户登录
3. 令牌刷新
4. 获取当前用户信息
5. 更新用户设置
6. 修改密码

认证流程说明：
┌─────────────────────────────────────────────────────────────────────────┐
│                            用户登录流程                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐     POST /login      ┌──────────┐                         │
│  │  客户端   │ ──────────────────> │  服务器   │                         │
│  │          │  {email, password}  │          │                         │
│  │          │                      │          │                         │
│  │          │  <────────────────── │          │                         │
│  │          │  {accessToken,       │          │                         │
│  └──────────┘   refreshToken}      └──────────┘                         │
│       │                                                                  │
│       │ 保存令牌到 localStorage                                          │
│       ▼                                                                  │
│  ┌──────────┐     GET /api/*        ┌──────────┐                        │
│  │  客户端   │ ──────────────────>  │  服务器   │                        │
│  │          │  Authorization:       │          │                        │
│  │          │  Bearer <token>       │          │                        │
│  └──────────┘                       └──────────┘                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

令牌刷新流程：
- 访问令牌过期后，使用刷新令牌获取新的访问令牌
- 无需用户重新输入密码
- 刷新令牌过期后，用户需要重新登录

安全措施：
- 密码使用 bcrypt 哈希存储
- 登录接口有速率限制（10次/分钟）
- 错误信息不区分用户名/密码错误，防止枚举
"""

# APIRouter: 创建路由器实例，用于组织 API 端点
# HTTPException: HTTP 异常类，用于返回错误响应
# Request: HTTP 请求对象，用于访问请求信息（如速率限制）
# status: HTTP 状态码常量集合
from fastapi import APIRouter, HTTPException, Request, status

# Limiter: 速率限制器类，用于防止 API 滥用
from slowapi import Limiter

# get_remote_address: 获取客户端 IP 地址的工具函数
from slowapi.util import get_remote_address

# CurrentUserId: 当前认证用户 ID 的类型别名（依赖注入）
# CosmosDB: Cosmos DB 服务的类型别名（依赖注入）
from app.core.dependencies import CurrentUserId, CosmosDB

# create_access_token: 创建 JWT 访问令牌
# create_refresh_token: 创建 JWT 刷新令牌
# get_password_hash: 使用 bcrypt 对密码进行哈希
# verify_password: 验证密码是否与哈希匹配
# verify_token: 验证 JWT 令牌并返回用户 ID
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)

# PasswordChange: 修改密码请求的数据模型
# TokenRefresh: 令牌刷新请求的数据模型
# TokenResponse: 认证成功响应的数据模型（包含用户信息和令牌）
# UserCreate: 用户注册请求的数据模型
# UserLogin: 用户登录请求的数据模型
# UserResponse: 用户信息响应的数据模型
# UserSettingsUpdate: 更新用户设置请求的数据模型
from app.schemas.auth import (
    PasswordChange,
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserSettingsUpdate,
)

# 创建路由器实例
# 这个路由器会被注册到 /api/auth 路径下
router = APIRouter()

# 创建速率限制器
# 使用客户端 IP 地址作为限制的唯一标识
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# 注册功能（已禁用）
# ============================================================================
# 下面是原始的注册功能代码，目前已禁用
# 如需启用，取消注释并删除 register_disabled 函数

# @router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
# @limiter.limit("5/minute")  # 限制每分钟 5 次注册请求
# async def register(request: Request, user_data: UserCreate, db: CosmosDB) -> TokenResponse:
#     """
#     注册新用户。
#
#     创建新用户账户并返回认证令牌。
#     """
#     # 检查邮箱是否已被注册
#     existing_user = await db.get_user_by_email(user_data.email)
#     if existing_user:
#         raise HTTPException(
#             status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#             detail="该邮箱已被注册",
#         )
#
#     # 创建用户
#     user = await db.create_user({
#         "email": user_data.email,
#         "username": user_data.username,
#         "passwordHash": get_password_hash(user_data.password),
#     })
#
#     # 生成令牌
#     access_token = create_access_token(subject=user["id"])
#     refresh_token = create_refresh_token(subject=user["id"])
#
#     return TokenResponse(
#         user=UserResponse(
#             id=user["id"],
#             email=user["email"],
#             username=user["username"],
#             createdAt=user["createdAt"],
#             settings=user.get("settings"),
#         ),
#         accessToken=access_token,
#         refreshToken=refresh_token,
#         expiresIn=86400,  # 24 小时（秒）
#     )


@router.post("/register", response_model=dict, status_code=status.HTTP_403_FORBIDDEN)
async def register_disabled(request: Request) -> dict:
    """
    注册功能占位端点（已禁用）。
    
    由于安全考虑，公开注册功能已暂时关闭。
    新用户需要联系管理员通过脚本创建账户。
    
    Args:
        request: FastAPI 请求对象
        
    Raises:
        HTTPException: 总是返回 403 Forbidden
    """
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="注册功能已暂时关闭，请联系管理员获取账户",
    )


# ============================================================================
# 用户登录
# ============================================================================

@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")  # 限制每分钟 10 次登录尝试，防止暴力破解
async def login(request: Request, credentials: UserLogin, db: CosmosDB) -> TokenResponse:
    """
    用户登录。
    
    验证用户凭证，成功后返回访问令牌和刷新令牌。
    
    安全措施：
    - 速率限制：每分钟最多 10 次尝试
    - 统一错误信息：无论用户名还是密码错误，都返回相同信息
    - 密码验证使用恒定时间比较，防止时序攻击
    
    Args:
        request: FastAPI 请求对象（用于速率限制）
        credentials: 登录凭证（email 和 password）
        db: Cosmos DB 服务实例（依赖注入）
        
    Returns:
        TokenResponse: 包含用户信息和令牌的响应
        
    Raises:
        HTTPException: 401 错误，当凭证无效时
    """
    # 根据邮箱查找用户
    user = await db.get_user_by_email(credentials.email)
    if not user:
        # 用户不存在，返回统一错误信息
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    # 验证密码
    if not verify_password(credentials.password, user["passwordHash"]):
        # 密码错误，返回相同的错误信息（防止用户枚举）
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    # 认证成功，生成令牌
    access_token = create_access_token(subject=user["id"])
    refresh_token = create_refresh_token(subject=user["id"])

    # 返回用户信息和令牌
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
        expiresIn=86400,  # 24 小时（秒）
    )


# ============================================================================
# 令牌刷新
# ============================================================================

@router.post("/refresh", response_model=dict)
async def refresh_token(token_data: TokenRefresh) -> dict:
    """
    使用刷新令牌获取新的访问令牌。
    
    访问令牌过期后，客户端可以使用此端点获取新的访问令牌，
    无需用户重新输入密码。
    
    使用流程：
    1. 客户端检测到访问令牌过期（401 错误或本地检查）
    2. 使用保存的刷新令牌调用此端点
    3. 获取新的访问令牌继续使用
    4. 刷新令牌过期后，用户需要重新登录
    
    Args:
        token_data: 包含 refreshToken 的请求体
        
    Returns:
        dict: 包含新访问令牌的响应
        
    Raises:
        HTTPException: 401 错误，当刷新令牌无效或过期时
    """
    # 验证刷新令牌
    user_id = verify_token(token_data.refreshToken, token_type="refresh")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或已过期的刷新令牌",
        )

    # 生成新的访问令牌
    access_token = create_access_token(subject=user_id)

    return {
        "success": True,
        "data": {
            "accessToken": access_token,
            "expiresIn": 86400,  # 24 小时（秒）
        },
    }


# ============================================================================
# 获取当前用户信息
# ============================================================================

@router.get("/me", response_model=dict)
async def get_current_user(user_id: CurrentUserId, db: CosmosDB) -> dict:
    """
    获取当前登录用户的信息。
    
    需要有效的访问令牌。通常在应用启动时调用，
    用于验证令牌有效性并获取用户数据。
    
    Args:
        user_id: 从令牌中提取的用户 ID（依赖注入）
        db: Cosmos DB 服务实例（依赖注入）
        
    Returns:
        dict: 包含用户信息的响应
        
    Raises:
        HTTPException: 404 错误，当用户不存在时（理论上不应发生）
    """
    # 根据 ID 获取用户信息
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


# ============================================================================
# 更新用户设置
# ============================================================================

@router.put("/settings", response_model=dict)
async def update_settings(
    settings: UserSettingsUpdate,
    user_id: CurrentUserId,
    db: CosmosDB,
) -> dict:
    """
    更新当前用户的设置。
    
    允许用户更新偏好设置，如默认模型、主题等。
    
    Args:
        settings: 要更新的设置（Pydantic 模型）
        user_id: 从令牌中提取的用户 ID
        db: Cosmos DB 服务实例
        
    Returns:
        dict: 包含更新后设置的响应
        
    Raises:
        HTTPException: 404 错误，当用户不存在时
    """
    # 只更新非 None 的字段
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


# ============================================================================
# 修改密码
# ============================================================================

@router.put("/password", response_model=dict)
async def change_password(
    password_data: PasswordChange,
    user_id: CurrentUserId,
    db: CosmosDB,
) -> dict:
    """
    修改当前用户的密码。
    
    需要提供当前密码进行验证，然后设置新密码。
    
    安全措施：
    - 必须验证当前密码
    - 新密码会使用 bcrypt 重新哈希
    - 不会使现有令牌失效（可根据需要添加此功能）
    
    Args:
        password_data: 包含当前密码和新密码的请求体
        user_id: 从令牌中提取的用户 ID
        db: Cosmos DB 服务实例
        
    Returns:
        dict: 成功消息
        
    Raises:
        HTTPException:
            - 404: 用户不存在
            - 401: 当前密码错误
    """
    # 获取用户信息
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    # 验证当前密码
    if not verify_password(password_data.currentPassword, user["passwordHash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="当前密码错误",
        )

    # 更新为新密码（使用 bcrypt 哈希）
    await db.update_user(user_id, {
        "passwordHash": get_password_hash(password_data.newPassword),
    })

    return {
        "success": True,
        "message": "密码已更新",
    }