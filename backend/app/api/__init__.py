"""API routes for the application."""

from fastapi import APIRouter

from app.api import auth, conversations, chat, files

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["会话"])
api_router.include_router(chat.router, tags=["聊天"])
api_router.include_router(files.router, prefix="/files", tags=["文件"])