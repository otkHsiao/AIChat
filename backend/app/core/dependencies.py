"""
FastAPI 依赖注入工具模块。

本模块定义了应用程序中可重用的依赖项（Dependencies），
用于 FastAPI 的依赖注入系统。依赖注入是一种设计模式，
它允许我们将通用逻辑（如认证、数据库访问）抽取出来复用。

主要功能：
1. 用户认证：从请求头提取和验证 JWT 令牌
2. 数据库访问：提供 Cosmos DB 服务的单例实例

使用方式：
    from app.core.dependencies import CurrentUserId, CosmosDB
    
    @router.get("/protected")
    async def protected_route(user_id: CurrentUserId, db: CosmosDB):
        # user_id 已经过验证
        # db 是已初始化的数据库服务
        pass

FastAPI 依赖注入的工作原理：
1. 定义依赖函数（如 get_current_user_id）
2. 使用 Depends() 将其声明为依赖
3. FastAPI 在处理请求前自动调用依赖函数
4. 依赖函数的返回值注入到路由处理函数中

类型别名的优势：
- CurrentUserId = Annotated[str, Depends(get_current_user_id)]
- 简化函数签名，提高代码可读性
- 统一依赖的使用方式
"""

# Annotated: 类型注解增强工具，用于为类型添加元数据（如依赖注入）
# Optional: 类型注解，表示可选值
from typing import Annotated, Optional

# Depends: FastAPI 依赖注入装饰器，用于声明函数依赖
# HTTPException: HTTP 异常类，用于返回错误响应
# status: HTTP 状态码常量集合
from fastapi import Depends, HTTPException, status

# HTTPAuthorizationCredentials: HTTP 认证凭证类，包含 Bearer Token
# HTTPBearer: HTTP Bearer 认证方案，自动从请求头提取 Token
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# verify_token: 验证 JWT 令牌并返回用户 ID
from app.core.security import verify_token

# CosmosDBService: Cosmos DB 数据库服务类
from app.services.cosmos_db import CosmosDBService

# ============================================================================
# HTTP Bearer 认证方案
# ============================================================================
# HTTPBearer 会自动从请求头中提取 "Authorization: Bearer <token>"
# 如果请求头不存在或格式错误，会返回 401 错误
security = HTTPBearer()


# ============================================================================
# 用户认证依赖
# ============================================================================

async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    """
    从 JWT 令牌中提取并验证当前用户 ID。
    
    这是一个强制认证依赖，如果令牌无效或不存在，
    会抛出 401 Unauthorized 异常。
    
    工作流程：
    1. HTTPBearer 从请求头提取 Bearer 令牌
    2. 调用 verify_token 验证令牌
    3. 返回用户 ID 或抛出异常
    
    请求头格式：
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    
    Args:
        credentials: HTTP Bearer 凭证，包含令牌字符串
        
    Returns:
        str: 经过验证的用户 ID
        
    Raises:
        HTTPException: 401 错误，当令牌无效或已过期时
        
    Example:
        @router.get("/profile")
        async def get_profile(user_id: str = Depends(get_current_user_id)):
            return {"user_id": user_id}
    """
    # 从凭证中提取令牌字符串
    token = credentials.credentials
    
    # 验证令牌并提取用户 ID
    user_id = verify_token(token, token_type="access")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            # WWW-Authenticate 头是 HTTP 规范要求的
            # 告知客户端需要 Bearer 认证
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


async def get_optional_user_id(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(HTTPBearer(auto_error=False))],
) -> Optional[str]:
    """
    可选的用户认证依赖。
    
    与 get_current_user_id 不同，此依赖不强制要求认证：
    - 如果提供了有效令牌，返回用户 ID
    - 如果未提供令牌，返回 None（不报错）
    - 如果提供了无效令牌，返回 None（不报错）
    
    使用场景：
    - 公开 API 但登录用户有额外功能
    - 记录用户行为（如果已登录）
    - 个性化响应（登录用户看到不同内容）
    
    Args:
        credentials: 可选的 HTTP Bearer 凭证
        
    Returns:
        Optional[str]: 用户 ID（如果令牌有效），否则 None
        
    Example:
        @router.get("/content")
        async def get_content(user_id: Optional[str] = Depends(get_optional_user_id)):
            if user_id:
                return {"message": f"Welcome, {user_id}!"}
            return {"message": "Welcome, guest!"}
    """
    if credentials is None:
        return None
    
    return verify_token(credentials.credentials, token_type="access")


# ============================================================================
# 类型别名定义
# ============================================================================
# 使用 Annotated 类型别名简化依赖注入的使用
# 这样在路由函数中可以直接使用类型注解，代码更简洁

# 强制认证的用户 ID
# 使用方式：async def route(user_id: CurrentUserId)
CurrentUserId = Annotated[str, Depends(get_current_user_id)]

# 可选认证的用户 ID
# 使用方式：async def route(user_id: OptionalUserId)
OptionalUserId = Annotated[Optional[str], Depends(get_optional_user_id)]


# ============================================================================
# 数据库服务依赖
# ============================================================================

# 全局数据库服务实例（单例模式）
# 使用全局变量确保整个应用共享同一个数据库连接
_cosmos_service: Optional[CosmosDBService] = None


async def get_cosmos_db() -> CosmosDBService:
    """
    获取 Cosmos DB 服务实例。
    
    实现单例模式：
    - 首次调用时创建并初始化服务实例
    - 后续调用直接返回已有实例
    
    这样做的好处：
    1. 避免重复建立数据库连接
    2. 复用连接池，提高性能
    3. 确保整个应用使用同一个服务实例
    
    初始化过程：
    1. 创建 CosmosDBService 实例
    2. 调用 initialize() 建立连接
    3. 创建数据库和容器（如果不存在）
    
    Returns:
        CosmosDBService: 已初始化的数据库服务实例
        
    Note:
        此依赖是异步的，因为数据库初始化需要异步操作
    """
    global _cosmos_service
    
    if _cosmos_service is None:
        # 首次调用，创建并初始化服务
        _cosmos_service = CosmosDBService()
        await _cosmos_service.initialize()
    
    return _cosmos_service


# Cosmos DB 服务类型别名
# 使用方式：async def route(db: CosmosDB)
CosmosDB = Annotated[CosmosDBService, Depends(get_cosmos_db)]