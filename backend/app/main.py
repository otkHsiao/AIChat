"""
FastAPI 应用程序入口点模块。

本模块是整个后端应用的主入口，负责：
1. 创建和配置 FastAPI 应用实例
2. 设置中间件（CORS、速率限制等）
3. 注册 API 路由
4. 配置全局异常处理
5. 管理应用生命周期（启动/关闭事件）

架构说明：
- 使用工厂模式 (create_application) 创建应用，便于测试和配置
- 使用 asynccontextmanager 管理异步资源的生命周期
- 集成 slowapi 实现 API 速率限制，防止滥用
- 支持开发/生产环境的差异化配置
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api import api_router
from app.core.config import get_settings
from app.core.dependencies import get_cosmos_db

# ============================================================================
# 速率限制器初始化
# ============================================================================
# 使用客户端 IP 地址作为限制的唯一标识符
# 这可以防止单个 IP 对 API 的过度调用
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用程序生命周期管理器。
    
    使用 Python 的异步上下文管理器模式来处理应用的启动和关闭事件。
    这是 FastAPI 推荐的现代生命周期管理方式，替代了旧版的 @app.on_event 装饰器。
    
    启动时执行的操作：
    - 加载应用配置
    - 初始化数据库连接池
    - 预热必要的服务
    
    关闭时执行的操作：
    - 清理数据库连接
    - 释放其他资源
    
    Args:
        app: FastAPI 应用实例
        
    Yields:
        None: 控制权交给应用运行，直到关闭信号
    """
    # ========== 启动阶段 ==========
    settings = get_settings()
    print(f"Starting AI Chat API in {settings.environment} mode...")
    
    # 初始化 Cosmos DB 连接
    # 这会创建数据库和容器（如果不存在）
    db = await get_cosmos_db()
    print("Cosmos DB connection initialized")
    
    # yield 将控制权交给应用，应用将开始处理请求
    yield
    
    # ========== 关闭阶段 ==========
    # 在这里执行清理操作
    print("Shutting down AI Chat API...")


def create_application() -> FastAPI:
    """
    创建并配置 FastAPI 应用实例。
    
    采用工厂模式创建应用，这种模式的优点：
    1. 便于在测试中创建隔离的应用实例
    2. 可以根据不同环境传入不同配置
    3. 配置逻辑集中管理，易于维护
    
    配置内容包括：
    - API 文档（仅在调试模式下启用）
    - CORS 跨域设置
    - 速率限制
    - 路由注册
    - 全局异常处理
    
    Returns:
        FastAPI: 配置完成的 FastAPI 应用实例
    """
    settings = get_settings()

    # ========== 创建 FastAPI 应用实例 ==========
    app = FastAPI(
        title="AI Chat API",
        description="类似 ChatGPT 的智能聊天应用后端 API",
        version="0.1.0",
        # 仅在调试模式下启用 Swagger UI 和 ReDoc 文档
        # 生产环境禁用以减少攻击面
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        # 使用生命周期管理器
        lifespan=lifespan,
    )

    # ========== 配置速率限制 ==========
    # 将限制器实例附加到应用状态
    app.state.limiter = limiter
    # 注册速率限制超出时的异常处理器
    # 当请求超出限制时，返回 429 Too Many Requests
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ========== 配置 CORS（跨源资源共享） ==========
    # CORS 允许前端应用从不同域名访问 API
    # 这对于前后端分离架构是必需的
    app.add_middleware(
        CORSMiddleware,
        # 允许的前端域名列表（从配置读取）
        allow_origins=settings.cors_origins_list,
        # 允许发送认证信息（cookies、Authorization 头等）
        allow_credentials=True,
        # 允许所有 HTTP 方法
        allow_methods=["*"],
        # 允许所有请求头
        allow_headers=["*"],
    )

    # ========== 注册 API 路由 ==========
    # 所有 API 路由都以 /api 为前缀
    # api_router 包含所有子路由（auth、conversations、chat、files）
    app.include_router(api_router, prefix="/api")

    # ========== 健康检查端点 ==========
    @app.get("/health")
    async def health_check():
        """
        健康检查端点，用于负载均衡器和容器编排系统。
        
        Azure App Service、Kubernetes 等平台会定期调用此端点
        来确认应用是否正常运行。如果返回非 2xx 状态码，
        平台可能会重启容器或将流量切换到其他实例。
        
        Returns:
            dict: 包含健康状态和当前环境的信息
        """
        return {"status": "healthy", "environment": settings.environment}

    # ========== 全局异常处理器 ==========
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        全局异常处理器，捕获所有未处理的异常。
        
        这是最后一道防线，确保即使发生意外错误，
        API 也能返回结构化的错误响应，而不是暴露内部错误信息。
        
        安全考虑：
        - 生产环境：只返回通用错误消息，隐藏技术细节
        - 开发环境：返回完整错误信息，便于调试
        
        Args:
            request: FastAPI 请求对象
            exc: 捕获到的异常
            
        Returns:
            JSONResponse: 统一格式的错误响应
        """
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    # 生产环境隐藏具体错误信息
                    "message": "服务器内部错误" if settings.is_production else str(exc),
                },
            },
        )

    return app


# ============================================================================
# 创建应用实例
# ============================================================================
# 这个全局变量会被 ASGI 服务器（如 uvicorn）使用
# 通过 "app.main:app" 引用
app = create_application()


# ============================================================================
# 开发服务器入口
# ============================================================================
if __name__ == "__main__":
    """
    直接运行本文件时启动开发服务器。
    
    使用方式：
        python -m app.main
        或
        python app/main.py
    
    注意：生产环境应使用 gunicorn 或 uvicorn 直接启动：
        uvicorn app.main:app --host 0.0.0.0 --port 8000
    """
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",  # 应用的导入路径
        host="0.0.0.0",  # 监听所有网络接口
        port=8000,       # 监听端口
        reload=settings.debug,  # 开发模式下启用热重载
    )