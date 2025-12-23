"""
对话管理 API 路由模块。

本模块处理对话（Conversation）的 CRUD 操作：
1. 列出对话 - 获取用户的所有对话列表
2. 创建对话 - 新建一个对话会话
3. 获取对话 - 获取单个对话的详情
4. 更新对话 - 修改对话标题或设置
5. 删除对话 - 删除对话及其所有消息

对话数据结构：
{
    "id": "uuid",              // 对话唯一标识
    "userId": "uuid",          // 所属用户 ID
    "title": "对话标题",        // 显示在侧边栏的标题
    "systemPrompt": "...",     // 系统提示词，设定 AI 行为
    "model": "gpt-4o",         // 使用的 AI 模型
    "messageCount": 10,        // 消息总数
    "createdAt": "ISO时间戳",
    "updatedAt": "ISO时间戳"
}

速率限制：
- 列表查询: 60 次/分钟
- 创建对话: 30 次/分钟
- 其他操作: 无限制（但受认证保护）
"""

# Optional: 类型注解，表示可选参数
from typing import Optional

# APIRouter: 创建路由器实例
# HTTPException: HTTP 异常类，用于返回错误响应
# Query: 查询参数声明器，用于定义 URL 查询参数及其验证规则
# Request: HTTP 请求对象
# status: HTTP 状态码常量集合
from fastapi import APIRouter, HTTPException, Query, Request, status

# Limiter: 速率限制器类
from slowapi import Limiter

# get_remote_address: 获取客户端 IP 地址的工具函数
from slowapi.util import get_remote_address

# CurrentUserId: 当前认证用户 ID 的类型别名（依赖注入）
# CosmosDB: Cosmos DB 服务的类型别名（依赖注入）
from app.core.dependencies import CurrentUserId, CosmosDB

# sanitize_conversation_title: 清理对话标题，防止 XSS 攻击
from app.core.sanitizer import sanitize_conversation_title

# ConversationCreate: 创建对话请求的数据模型
# ConversationDeleteResponse: 删除对话响应的数据模型
# ConversationListResponse: 对话列表响应的数据模型（包含分页信息）
# ConversationResponse: 单个对话响应的数据模型
# ConversationUpdate: 更新对话请求的数据模型
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDeleteResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
)

# 创建路由器实例
# 这个路由器会被注册到 /api/conversations 路径下
router = APIRouter()

# 创建速率限制器
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# 列出对话
# ============================================================================

@router.get("", response_model=dict)
@limiter.limit("60/minute")  # 限制每分钟 60 次请求
async def list_conversations(
    request: Request,
    user_id: CurrentUserId,
    db: CosmosDB,
    limit: int = Query(default=20, ge=1, le=100),  # 每页数量：1-100，默认 20
    offset: int = Query(default=0, ge=0),           # 跳过数量：>= 0，默认 0
) -> dict:
    """
    获取当前用户的所有对话列表。
    
    返回按更新时间倒序排列的分页对话列表。
    最近活跃的对话排在前面，便于用户快速访问。
    
    分页参数：
    - limit: 每页返回的对话数量（1-100）
    - offset: 跳过的对话数量（用于翻页）
    
    分页示例：
    - 第 1 页: ?limit=20&offset=0
    - 第 2 页: ?limit=20&offset=20
    - 第 3 页: ?limit=20&offset=40
    
    Args:
        request: FastAPI 请求对象
        user_id: 当前用户 ID（从令牌提取）
        db: Cosmos DB 服务实例
        limit: 每页数量
        offset: 跳过数量
        
    Returns:
        dict: 包含对话列表和分页信息的响应
    """
    # 获取对话列表
    conversations = await db.get_conversations_by_user(
        user_id=user_id,
        limit=limit,
        offset=offset,
    )

    # 获取对话总数（用于分页 UI）
    total = await db.count_conversations_by_user(user_id)

    return {
        "success": True,
        "data": ConversationListResponse(
            conversations=[
                ConversationResponse(**conv) for conv in conversations
            ],
            total=total,
            limit=limit,
            offset=offset,
        ),
    }


# ============================================================================
# 创建对话
# ============================================================================

@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")  # 限制每分钟 30 次创建
async def create_conversation(
    request: Request,
    conversation_data: ConversationCreate,
    user_id: CurrentUserId,
    db: CosmosDB,
) -> dict:
    """
    创建新对话。
    
    创建一个新的对话会话。对话创建后，用户可以在其中发送消息。
    
    可选参数：
    - title: 对话标题（默认"新对话"）
    - systemPrompt: 系统提示词（默认通用助手提示）
    - model: AI 模型（默认"gpt-4o"）
    
    安全措施：
    - 对标题进行清理，防止 XSS 攻击
    
    Args:
        request: FastAPI 请求对象
        conversation_data: 对话创建数据
        user_id: 当前用户 ID
        db: Cosmos DB 服务实例
        
    Returns:
        dict: 包含创建的对话信息的响应
    """
    # 清理输入数据，防止 XSS
    sanitized_data = conversation_data.model_dump()
    if sanitized_data.get("title"):
        sanitized_data["title"] = sanitize_conversation_title(sanitized_data["title"])
    
    # 创建对话
    conversation = await db.create_conversation(
        user_id=user_id,
        conversation_data=sanitized_data,
    )

    return {
        "success": True,
        "data": ConversationResponse(**conversation),
    }


# ============================================================================
# 获取单个对话
# ============================================================================

@router.get("/{conversation_id}", response_model=dict)
async def get_conversation(
    conversation_id: str,
    user_id: CurrentUserId,
    db: CosmosDB,
) -> dict:
    """
    获取指定对话的详情。
    
    根据对话 ID 获取对话信息。
    只能获取属于当前用户的对话（通过分区键验证）。
    
    Args:
        conversation_id: 对话 ID（路径参数）
        user_id: 当前用户 ID
        db: Cosmos DB 服务实例
        
    Returns:
        dict: 包含对话信息的响应
        
    Raises:
        HTTPException: 404 错误，当对话不存在或不属于当前用户时
    """
    # 获取对话（同时验证所有权）
    conversation = await db.get_conversation(conversation_id, user_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    return {
        "success": True,
        "data": ConversationResponse(**conversation),
    }


# ============================================================================
# 更新对话
# ============================================================================

@router.put("/{conversation_id}", response_model=dict)
async def update_conversation(
    conversation_id: str,
    conversation_data: ConversationUpdate,
    user_id: CurrentUserId,
    db: CosmosDB,
) -> dict:
    """
    更新对话的标题或系统提示词。
    
    允许用户修改对话的以下属性：
    - title: 对话标题
    - systemPrompt: 系统提示词
    - model: AI 模型
    
    只能更新属于当前用户的对话。
    
    Args:
        conversation_id: 对话 ID（路径参数）
        conversation_data: 要更新的字段
        user_id: 当前用户 ID
        db: Cosmos DB 服务实例
        
    Returns:
        dict: 包含更新后对话信息的响应
        
    Raises:
        HTTPException: 404 错误，当对话不存在或不属于当前用户时
    """
    # 检查对话是否存在
    existing = await db.get_conversation(conversation_id, user_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    # 更新对话（只更新非 None 的字段）
    updates = conversation_data.model_dump(exclude_none=True)
    conversation = await db.update_conversation(conversation_id, user_id, updates)

    return {
        "success": True,
        "data": ConversationResponse(**conversation),
    }


# ============================================================================
# 删除对话
# ============================================================================

@router.delete("/{conversation_id}", response_model=ConversationDeleteResponse)
async def delete_conversation(
    conversation_id: str,
    user_id: CurrentUserId,
    db: CosmosDB,
) -> ConversationDeleteResponse:
    """
    删除对话及其所有消息。
    
    这是一个级联删除操作：
    1. 删除对话文档
    2. 删除该对话下的所有消息
    
    删除后无法恢复，请谨慎操作。
    只能删除属于当前用户的对话。
    
    Args:
        conversation_id: 对话 ID（路径参数）
        user_id: 当前用户 ID
        db: Cosmos DB 服务实例
        
    Returns:
        ConversationDeleteResponse: 删除成功的响应
        
    Raises:
        HTTPException: 404 错误，当对话不存在或不属于当前用户时
    """
    # 删除对话
    success = await db.delete_conversation(conversation_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    # 返回成功响应
    return ConversationDeleteResponse()