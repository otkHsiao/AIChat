"""
安全工具模块 - 认证和密码处理。

本模块提供应用程序的核心安全功能：
1. 密码哈希和验证（使用 bcrypt）
2. JWT（JSON Web Token）令牌的创建和验证

安全设计说明：
- 密码使用 bcrypt 进行哈希，bcrypt 是专门为密码存储设计的算法
- bcrypt 自动处理盐值（salt），每次哈希都会生成不同的结果
- JWT 使用 HS256 对称加密算法，密钥存储在环境变量中
- 令牌包含过期时间，过期后自动失效

JWT 令牌类型：
- access: 访问令牌，用于 API 认证，有效期较短（24小时）
- refresh: 刷新令牌，用于获取新的访问令牌，有效期较长（7天）

令牌结构（Payload）：
{
    "sub": "user_id",      # 主题（用户ID）
    "exp": 1234567890,     # 过期时间戳
    "iat": 1234567890,     # 签发时间戳
    "type": "access"       # 令牌类型
}
"""

# datetime: 日期时间类，用于处理时间戳
# timedelta: 时间差类，用于计算令牌过期时间
# timezone: 时区类，用于 UTC 时间处理
from datetime import datetime, timedelta, timezone

# Any: 任意类型注解
# Optional: 可选类型注解
from typing import Any, Optional

# bcrypt: 密码哈希库，专为安全存储密码设计（自动处理盐值）
import bcrypt

# JWTError: JWT 相关异常类（签名无效、过期等）
# jwt: JWT 编码和解码工具
from jose import JWTError, jwt

# get_settings: 获取应用配置的函数
from app.core.config import get_settings


# ============================================================================
# 密码处理函数
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码是否与哈希密码匹配。
    
    使用 bcrypt 的 checkpw 函数进行安全比较。
    bcrypt 会自动从哈希密码中提取盐值进行验证。
    
    安全特性：
    - 使用恒定时间比较，防止时序攻击
    - 自动处理 Unicode 编码
    
    Args:
        plain_password: 用户输入的明文密码
        hashed_password: 数据库中存储的哈希密码
        
    Returns:
        bool: 密码匹配返回 True，否则返回 False
        
    Example:
        if verify_password("user_password", user.password_hash):
            print("密码正确")
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """
    使用 bcrypt 对密码进行哈希处理。
    
    bcrypt 是一种自适应哈希函数，特别适合密码存储：
    - 自动生成随机盐值
    - 可配置的计算成本因子
    - 抗暴力破解和彩虹表攻击
    
    默认使用的工作因子（work factor）为 12，
    这意味着 2^12 = 4096 次迭代。
    
    Args:
        password: 需要哈希的明文密码
        
    Returns:
        str: bcrypt 格式的哈希字符串
             格式：$2b$12$<22字符盐值><31字符哈希>
             
    Example:
        hash = get_password_hash("secure_password")
        # 返回类似: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4bHZR9.Y.JZq2gWe
    """
    # 生成随机盐值，默认 rounds=12
    salt = bcrypt.gensalt()
    # 使用盐值对密码进行哈希
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    # 将字节串转换为字符串以便存储
    return hashed.decode('utf-8')


# ============================================================================
# JWT 令牌处理函数
# ============================================================================

def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    extra_data: Optional[dict[str, Any]] = None,
) -> str:
    """
    创建 JWT 访问令牌。
    
    访问令牌用于 API 请求的身份验证，客户端需要在
    Authorization 头中携带此令牌：
    Authorization: Bearer <access_token>
    
    令牌结构：
    - sub (subject): 用户 ID
    - exp (expiration): 过期时间
    - iat (issued at): 签发时间
    - type: 令牌类型标识
    
    Args:
        subject: 令牌主题，通常是用户 ID
        expires_delta: 自定义过期时间间隔，默认使用配置的 jwt_expiration_hours
        extra_data: 需要包含在令牌中的额外数据
        
    Returns:
        str: 编码后的 JWT 令牌字符串
        
    Example:
        token = create_access_token(
            subject=user.id,
            extra_data={"role": "admin"}
        )
    """
    settings = get_settings()
    
    # 计算过期时间
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiration_hours)
    
    # 构建令牌载荷（payload）
    to_encode: dict[str, Any] = {
        "sub": subject,           # 主题（用户ID）
        "exp": expire,            # 过期时间
        "iat": datetime.now(timezone.utc),  # 签发时间
        "type": "access",         # 令牌类型
    }
    
    # 添加额外数据（如果有）
    if extra_data:
        to_encode.update(extra_data)
    
    # 使用密钥和算法对载荷进行签名
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
    """
    创建 JWT 刷新令牌。
    
    刷新令牌用于在访问令牌过期后获取新的访问令牌，
    无需用户重新输入密码。刷新令牌的有效期比访问令牌长。
    
    使用流程：
    1. 用户登录，获取 access_token 和 refresh_token
    2. 使用 access_token 访问 API
    3. access_token 过期后，使用 refresh_token 获取新的 access_token
    4. refresh_token 过期后，用户需要重新登录
    
    安全考虑：
    - 刷新令牌应该安全存储（如 httpOnly cookie）
    - 每次使用刷新令牌后可以轮换（Token Rotation）
    - 可以维护刷新令牌黑名单用于撤销
    
    Args:
        subject: 令牌主题，通常是用户 ID
        
    Returns:
        str: 编码后的 JWT 刷新令牌字符串
    """
    settings = get_settings()
    
    # 刷新令牌使用更长的过期时间
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_expiration_days)
    
    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",  # 标记为刷新令牌
    }
    
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """
    解码并验证 JWT 令牌。
    
    验证过程包括：
    1. 验证签名是否有效
    2. 验证令牌是否过期
    3. 验证令牌格式是否正确
    
    Args:
        token: JWT 令牌字符串
        
    Returns:
        Optional[dict]: 解码后的令牌载荷，验证失败返回 None
        
    Note:
        此函数不验证令牌类型，调用者需要根据需要检查 "type" 字段
    """
    settings = get_settings()
    
    try:
        # jose 库会自动验证签名和过期时间
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        # 捕获所有 JWT 相关错误（签名无效、过期、格式错误等）
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """
    验证 JWT 令牌并返回用户 ID。
    
    这是一个高级验证函数，除了基本的令牌验证外，
    还会检查令牌类型是否匹配。
    
    使用场景：
    - 验证访问令牌：verify_token(token, "access")
    - 验证刷新令牌：verify_token(token, "refresh")
    
    Args:
        token: JWT 令牌字符串
        token_type: 期望的令牌类型，"access" 或 "refresh"
        
    Returns:
        Optional[str]: 验证成功返回用户 ID（sub 字段），
                       验证失败返回 None
                       
    Example:
        user_id = verify_token(request.headers["Authorization"].split()[1])
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    """
    # 首先解码令牌
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    # 验证令牌类型
    if payload.get("type") != token_type:
        return None
    
    # 返回用户 ID
    return payload.get("sub")