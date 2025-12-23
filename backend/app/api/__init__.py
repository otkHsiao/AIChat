"""API routes for the application."""

# APIRouter: FastAPI 的路由器类，用于组织和分组 API 端点
from fastapi import APIRouter

# 导入各个 API 子模块
# auth: 认证相关路由（登录、注册、令牌刷新等）
# conversations: 对话管理路由（创建、列表、删除对话）
# chat: 聊天消息路由（发送消息、流式响应）
# files: 文件上传路由（上传图片和文档）
from app.api import auth, conversations, chat, files

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["会话"])
api_router.include_router(chat.router, tags=["聊天"])
api_router.include_router(files.router, prefix="/files", tags=["文件"])