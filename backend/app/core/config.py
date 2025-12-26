"""
应用配置管理模块。

本模块使用 Pydantic Settings 来管理应用程序的所有配置。
Pydantic Settings 提供了以下优势：
1. 类型安全：所有配置项都有明确的类型定义
2. 自动验证：在启动时验证配置值的有效性
3. 环境变量支持：自动从环境变量读取配置
4. .env 文件支持：支持从 .env 文件加载配置
5. 默认值支持：可以为配置项设置默认值

配置优先级（从高到低）：
1. 环境变量
2. .env.local 文件
3. .env 文件
4. 默认值

安全说明：
- 敏感配置（API 密钥、数据库凭证等）应存储在 Azure Key Vault
- 生产环境使用 Key Vault 引用注入环境变量
- 本地开发使用 .env 文件（不要提交到版本控制）
"""

# lru_cache: 函数装饰器，用于缓存函数返回值（实现单例模式）
from functools import lru_cache

# List: 类型注解，表示列表类型
from typing import List

# BaseSettings: Pydantic 的配置基类，自动从环境变量加载配置
# SettingsConfigDict: 配置字典类型，用于定义 Pydantic Settings 的行为
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用程序配置类。
    
    继承自 Pydantic 的 BaseSettings，自动从环境变量加载配置。
    所有配置项都有类型注解，Pydantic 会自动进行类型转换和验证。
    
    使用方式：
        settings = get_settings()
        api_key = settings.azure_openai_api_key
    
    环境变量命名规则：
    - 配置项名称自动转换为大写
    - 例如：azure_openai_api_key -> AZURE_OPENAI_API_KEY
    """

    # Pydantic Settings 配置
    model_config = SettingsConfigDict(
        # 环境文件路径（按顺序加载，后面的覆盖前面的）
        env_file=(".env", ".env.local"),
        # 环境文件编码
        env_file_encoding="utf-8",
        # 环境变量名称不区分大小写
        case_sensitive=False,
        # 忽略未定义的额外字段（避免因多余的环境变量报错）
        extra="ignore",
    )

    # ========================================================================
    # 🔐 敏感密钥配置
    # 这些配置在生产环境应存储在 Azure Key Vault 中
    # ========================================================================
    
    # Azure OpenAI API 密钥
    # 用于调用 GPT-4o 模型进行对话生成
    azure_openai_api_key: str
    
    # Cosmos DB 主密钥
    # 用于访问 Azure Cosmos DB 数据库
    cosmos_db_key: str
    
    # Azure Blob Storage 连接字符串
    # 格式：DefaultEndpointsProtocol=https;AccountName=xxx;AccountKey=xxx;EndpointSuffix=core.windows.net
    azure_storage_connection_string: str
    
    # JWT 签名密钥
    # 用于签名和验证 JWT 令牌，应使用足够长的随机字符串
    jwt_secret_key: str

    # ========================================================================
    # Azure OpenAI 服务配置
    # ========================================================================
    
    # Azure OpenAI 服务端点 URL
    # 格式：https://<resource-name>.openai.azure.com/
    azure_openai_endpoint: str
    
    # 部署的模型名称（在 Azure OpenAI Studio 中创建的部署名）
    azure_openai_deployment_name: str = "gpt-4o"
    
    # API 版本（用于确保 API 兼容性）
    azure_openai_api_version: str = "2024-08-06"

    # ========================================================================
    # Azure Cosmos DB 配置
    # ========================================================================
    
    # Cosmos DB 账户端点
    # 格式：https://<account-name>.documents.azure.com:443/
    cosmos_db_endpoint: str
    
    # 数据库名称
    cosmos_db_database_name: str = "ai-chat-db"

    # ========================================================================
    # Azure Blob Storage 配置
    # ========================================================================
    
    # 存储容器名称（用于存储用户上传的文件）
    azure_storage_container_name: str = "uploads"

    # ========================================================================
    # JWT（JSON Web Token）配置
    # ========================================================================
    
    # JWT 签名算法
    # HS256：HMAC-SHA256，对称加密算法
    jwt_algorithm: str = "HS256"
    
    # 访问令牌过期时间（小时）
    # 24 小时后用户需要使用刷新令牌获取新的访问令牌
    jwt_expiration_hours: int = 24
    
    # 刷新令牌过期时间（天）
    # 7 天后用户需要重新登录
    jwt_refresh_expiration_days: int = 7

    # ========================================================================
    # CORS（跨域资源共享）配置
    # ========================================================================
    
    # 允许的前端域名（逗号分隔）
    # 这些域名的前端应用可以访问 API
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # ========================================================================
    # 应用程序配置
    # ========================================================================
    
    # 运行环境：development / staging / production
    environment: str = "development"
    
    # 调试模式
    # True：启用 API 文档、详细错误信息
    # False：禁用 API 文档、隐藏错误详情
    debug: bool = True

    @property
    def cors_origins_list(self) -> List[str]:
        """
        将 CORS 源字符串解析为列表。
        
        将逗号分隔的域名字符串转换为列表格式，
        供 FastAPI 的 CORSMiddleware 使用。
        
        Returns:
            List[str]: 允许的域名列表
            
        Example:
            "http://localhost:3000,http://localhost:5173"
            -> ["http://localhost:3000", "http://localhost:5173"]
        """
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """
        检查是否为生产环境。
        
        用于控制生产环境特有的行为，例如：
        - 禁用 API 文档
        - 隐藏详细错误信息
        - 启用更严格的安全策略
        
        Returns:
            bool: 如果是生产环境返回 True
        """
        return self.environment.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    获取应用配置的单例实例。
    
    使用 functools.lru_cache 装饰器确保配置只加载一次，
    后续调用直接返回缓存的实例。这样做的好处：
    1. 避免重复读取环境变量和配置文件
    2. 确保整个应用使用同一份配置
    3. 提高性能
    
    Returns:
        Settings: 配置实例
        
    Usage:
        from app.core.config import get_settings
        
        settings = get_settings()
        print(settings.azure_openai_endpoint)
    """
    return Settings()  # type: ignore[call-arg]