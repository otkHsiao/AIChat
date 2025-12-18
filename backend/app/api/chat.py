"""
聊天 API 路由模块 - 消息发送和流式响应。

本模块是应用的核心功能模块，处理：
1. 获取消息历史 - 加载对话中的历史消息
2. 发送消息（非流式）- 发送消息并等待完整回复
3. 发送消息（流式）- 发送消息并获取实时流式回复

消息数据结构：
{
    "id": "uuid",              // 消息唯一标识
    "conversationId": "uuid",  // 所属对话 ID
    "role": "user|assistant",  // 发送者角色
    "content": "消息内容",      // 文本内容
    "attachments": [...],      // 附件列表（图片等）
    "tokens": {                // 令牌使用统计
        "input": 100,
        "output": 200
    },
    "createdAt": "ISO时间戳"
}

流式响应机制（SSE - Server-Sent Events）：
┌─────────────────────────────────────────────────────────────────────────┐
│                        流式响应工作流程                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐  POST /messages/stream   ┌──────────┐  OpenAI API        │
│  │  前端     │ ─────────────────────>  │  后端     │ ───────────>       │
│  │          │                          │          │                     │
│  │          │  <─ event: message_start │          │                     │
│  │          │  <─ event: content_delta │          │  <── stream         │
│  │          │  <─ event: content_delta │          │  <── stream         │
│  │          │  <─ event: content_delta │          │  <── stream         │
│  │          │  <─ event: message_end   │          │                     │
│  └──────────┘                          └──────────┘                     │
│       │                                                                  │
│       │ 实时显示 AI 回复                                                  │
│       ▼                                                                  │
│  ┌──────────────────────────────────────┐                               │
│  │  用户看到 AI 逐字输出回复              │                               │
│  └──────────────────────────────────────┘                               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

SSE 事件类型：
- message_start: 开始生成，包含用户消息 ID
- content_delta: 内容增量，包含新生成的文本片段
- message_end: 生成完成，包含完整消息 ID 和令牌统计
- error: 发生错误

附件处理：
- 图片：直接传给 GPT-4o Vision 分析
- 文本文件：下载内容后作为上下文传给 AI
"""

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.dependencies import CurrentUserId, CosmosDB
from app.schemas.message import (
    ChatRequest,
    ChatResponse,
    MessageListResponse,
    MessageResponse,
)
from app.services.azure_openai import get_openai_service
from app.services.blob_storage import get_blob_service

# 创建路由器实例
router = APIRouter()

# 创建速率限制器
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# 获取消息历史
# ============================================================================

@router.get("/conversations/{conversation_id}/messages", response_model=dict)
@limiter.limit("60/minute")  # 限制每分钟 60 次请求
async def get_messages(
    request: Request,
    conversation_id: str,
    user_id: CurrentUserId,
    db: CosmosDB,
    limit: int = Query(default=50, ge=1, le=200),
    before: Optional[str] = Query(default=None, description="获取此消息ID之前的消息"),
) -> dict:
    """
    获取对话的消息历史。
    
    返回指定对话中的消息列表，支持分页加载。
    消息按时间正序排列（最早的在前）。
    
    分页策略：
    - 使用 before 参数实现"加载更多"功能
    - 返回 hasMore 标识是否还有更多消息
    
    Args:
        request: FastAPI 请求对象
        conversation_id: 对话 ID
        user_id: 当前用户 ID
        db: Cosmos DB 服务实例
        limit: 返回的最大消息数（1-200，默认 50）
        before: 获取此消息 ID 之前的消息（用于"加载更多"）
        
    Returns:
        dict: 包含消息列表和分页信息的响应
        
    Raises:
        HTTPException: 404 错误，当对话不存在时
    """
    # 验证对话属于当前用户
    conversation = await db.get_conversation(conversation_id, user_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    # 获取消息列表
    # 多获取一条用于判断是否还有更多
    messages = await db.get_messages_by_conversation(
        conversation_id=conversation_id,
        limit=limit + 1,
        before_id=before,
    )

    # 判断是否还有更多消息
    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]

    return {
        "success": True,
        "data": MessageListResponse(
            messages=[MessageResponse(**msg) for msg in messages],
            hasMore=has_more,
        ),
    }


# ============================================================================
# 发送消息（非流式）
# ============================================================================

@router.post("/conversations/{conversation_id}/messages", response_model=dict)
@limiter.limit("20/minute")  # 限制每分钟 20 次消息发送
async def send_message(
    request: Request,
    conversation_id: str,
    chat_request: ChatRequest,
    user_id: CurrentUserId,
    db: CosmosDB,
) -> dict:
    """
    发送消息并获取非流式响应。
    
    完整的消息处理流程：
    1. 验证对话所有权
    2. 获取历史消息作为上下文
    3. 保存用户消息
    4. 调用 AI API 获取回复
    5. 保存 AI 回复
    6. 更新对话消息计数
    
    注意：此端点会等待 AI 完成整个回复后才返回。
    对于更好的用户体验，推荐使用流式端点 /messages/stream。
    
    Args:
        request: FastAPI 请求对象
        conversation_id: 对话 ID
        chat_request: 聊天请求，包含消息内容和附件
        user_id: 当前用户 ID
        db: Cosmos DB 服务实例
        
    Returns:
        dict: 包含用户消息和 AI 回复的响应
        
    Raises:
        HTTPException: 404 错误，当对话不存在时
    """
    # 验证对话属于当前用户
    conversation = await db.get_conversation(conversation_id, user_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    # 获取历史消息作为上下文（最近 20 条）
    history = await db.get_messages_by_conversation(conversation_id, limit=20)

    # 处理附件
    attachments = []
    if chat_request.attachments:
        blob_service = get_blob_service()
        for att in chat_request.attachments:
            # 获取附件的 URL
            # TODO: 在实际实现中，应该从数据库查询 blob 名称
            attachments.append({
                "type": att.type,
                "url": f"placeholder-url-for-{att.id}",
            })

    # 保存用户消息
    user_message = await db.create_message(
        conversation_id=conversation_id,
        message_data={
            "role": "user",
            "content": chat_request.content,
            "attachments": [att.model_dump() for att in (chat_request.attachments or [])],
        },
    )

    # 调用 AI API 获取回复
    openai_service = get_openai_service()
    
    # 构建 API 需要的历史消息格式
    history_for_api = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in history
        if msg["role"] in ("user", "assistant")
    ]

    response = await openai_service.chat_completion(
        system_prompt=conversation["systemPrompt"],
        history=history_for_api,
        user_message=chat_request.content,
        attachments=attachments if attachments else None,
    )

    # 保存 AI 回复
    assistant_message = await db.create_message(
        conversation_id=conversation_id,
        message_data={
            "role": "assistant",
            "content": response["content"],
            "tokens": response["tokens"],
        },
    )

    # 更新对话消息计数（+2：用户消息 + AI 回复）
    await db.update_conversation(
        conversation_id,
        user_id,
        {"messageCount": conversation["messageCount"] + 2},
    )

    return {
        "success": True,
        "data": ChatResponse(
            userMessage=MessageResponse(**user_message),
            assistantMessage=MessageResponse(**assistant_message),
        ),
    }


# ============================================================================
# 发送消息（流式响应）
# ============================================================================

@router.post("/conversations/{conversation_id}/messages/stream")
@limiter.limit("20/minute")  # 限制每分钟 20 次消息发送
async def send_message_stream(
    request: Request,
    conversation_id: str,
    chat_request: ChatRequest,
    user_id: CurrentUserId,
    db: CosmosDB,
) -> StreamingResponse:
    """
    发送消息并获取流式响应（SSE）。
    
    这是推荐的消息发送方式，提供更好的用户体验：
    - AI 回复会实时显示，用户无需等待完整响应
    - 通过 Server-Sent Events (SSE) 实现
    - 前端可以逐字显示 AI 的回复
    
    处理流程：
    1. 验证对话所有权
    2. 获取历史消息作为上下文
    3. 立即保存用户消息
    4. 返回 SSE 流响应
    5. 在流中：
       - 发送 message_start 事件
       - 逐块发送 content_delta 事件
       - 完成后保存 AI 回复
       - 发送 message_end 事件
    
    附件处理：
    - 图片：传给 GPT-4o Vision 分析
    - 文本文件：下载内容后作为上下文附加到消息中
    
    Args:
        request: FastAPI 请求对象
        conversation_id: 对话 ID
        chat_request: 聊天请求，包含消息内容和附件
        user_id: 当前用户 ID
        db: Cosmos DB 服务实例
        
    Returns:
        StreamingResponse: SSE 流响应
        
    Raises:
        HTTPException: 404 错误，当对话不存在时
    """
    # 验证对话属于当前用户
    conversation = await db.get_conversation(conversation_id, user_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    # 获取历史消息作为上下文（最近 20 条）
    history = await db.get_messages_by_conversation(conversation_id, limit=20)

    # 立即保存用户消息（不等待 AI 回复）
    # 这样即使 AI 回复失败，用户消息也不会丢失
    user_message = await db.create_message(
        conversation_id=conversation_id,
        message_data={
            "role": "user",
            "content": chat_request.content,
            "attachments": [att.model_dump() for att in (chat_request.attachments or [])],
        },
    )

    async def generate():
        """
        SSE 事件生成器。
        
        这是一个异步生成器，产生符合 SSE 格式的事件字符串。
        
        SSE 格式：
        event: <event_name>
        data: <json_data>
        
        （两个换行符分隔事件）
        """
        openai_service = get_openai_service()
        blob_service = get_blob_service()
        
        # 构建 API 需要的历史消息格式
        history_for_api = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
            if msg["role"] in ("user", "assistant")
        ]

        # ========== 处理附件 ==========
        # 图片和文本文件需要不同的处理方式
        image_attachments = []      # 图片传给 Vision API
        text_file_contents = []     # 文本文件内容嵌入消息
        
        if chat_request.attachments:
            for att in chat_request.attachments:
                if att.type == "image" and att.url:
                    # 图片：直接传 URL 给 GPT-4o Vision
                    image_attachments.append({
                        "type": "image",
                        "url": att.url,
                    })
                elif att.type == "file" and att.url:
                    # 文本文件：下载内容并嵌入消息
                    # 判断是否为文本文件
                    mime_type = att.mimeType or ""
                    is_text_file = mime_type in (
                        "text/plain",
                        "text/markdown",
                        "application/octet-stream",  # 可能是文本
                    ) or (att.fileName and att.fileName.endswith((".md", ".txt")))
                    
                    if is_text_file:
                        # 下载文件内容
                        file_content = await blob_service.download_text_file(att.url)
                        if file_content:
                            file_name = att.fileName or "uploaded_file"
                            text_file_contents.append({
                                "fileName": file_name,
                                "content": file_content,
                            })

        # ========== 构建增强的用户消息 ==========
        # 如果有文本文件，将其内容附加到用户消息中
        enhanced_message = chat_request.content
        
        # 如果只有图片没有文字，添加默认提示
        if not enhanced_message.strip() and image_attachments:
            enhanced_message = "请描述并分析这张图片的内容。"
        
        # 将文本文件内容添加到消息末尾
        if text_file_contents:
            file_context = "\n\n---\n以下是用户上传的文件内容：\n"
            for file_info in text_file_contents:
                file_context += f"\n【文件: {file_info['fileName']}】\n```\n{file_info['content']}\n```\n"
            if enhanced_message:
                enhanced_message = enhanced_message + file_context
            else:
                enhanced_message = "请分析以下文件内容：" + file_context

        # ========== 发送 SSE 事件 ==========
        message_id = None
        
        # 1. 发送开始事件
        yield f"event: message_start\ndata: {json.dumps({'userMessageId': user_message['id']})}\n\n"

        full_content = ""  # 累积完整的 AI 回复
        tokens = {"input": 0, "output": 0}

        try:
            # 2. 流式获取 AI 回复
            async for chunk in openai_service.chat_completion_stream(
                system_prompt=conversation["systemPrompt"],
                history=history_for_api,
                user_message=enhanced_message,
                attachments=image_attachments if image_attachments else None,
            ):
                if chunk["type"] == "content_delta":
                    # 累积内容并发送增量
                    full_content += chunk["delta"]
                    yield f"event: content_delta\ndata: {json.dumps({'delta': chunk['delta']})}\n\n"

                elif chunk["type"] == "finish":
                    # AI 回复完成，保存到数据库
                    assistant_message = await db.create_message(
                        conversation_id=conversation_id,
                        message_data={
                            "role": "assistant",
                            "content": full_content,
                            "tokens": tokens,
                        },
                    )
                    message_id = assistant_message["id"]

                    # ========== 智能标题生成 ==========
                    # 如果是对话的第一条消息，生成语义化标题
                    new_title = None
                    if conversation["messageCount"] == 0:
                        try:
                            # 确定用于生成标题的内容
                            title_content = chat_request.content.strip()
                            if not title_content:
                                # 没有文字内容时使用默认标题
                                if image_attachments:
                                    title_content = "图片分析对话"
                                elif text_file_contents:
                                    title_content = f"文件分析: {text_file_contents[0]['fileName']}"
                                else:
                                    title_content = "新对话"
                            
                            # 使用 AI 生成标题
                            new_title = await openai_service.generate_conversation_title(
                                title_content
                            )
                            
                            # 更新对话标题和消息计数
                            await db.update_conversation(
                                conversation_id,
                                user_id,
                                {
                                    "messageCount": 2,
                                    "title": new_title,
                                },
                            )
                        except Exception as e:
                            # 标题生成失败不影响主流程
                            await db.update_conversation(
                                conversation_id,
                                user_id,
                                {"messageCount": 2},
                            )
                    else:
                        # 非首条消息，只更新消息计数
                        await db.update_conversation(
                            conversation_id,
                            user_id,
                            {"messageCount": conversation["messageCount"] + 2},
                        )

                    # 3. 发送完成事件
                    end_data = {'messageId': message_id, 'tokens': tokens}
                    if new_title:
                        # 如果生成了新标题，一并返回
                        end_data['conversationTitle'] = new_title
                    
                    yield f"event: message_end\ndata: {json.dumps(end_data)}\n\n"

        except Exception as e:
            # 发送错误事件
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    # 返回 SSE 流响应
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",  # SSE 的 MIME 类型
        headers={
            # 禁用缓存，确保实时传输
            "Cache-Control": "no-cache",
            # 保持连接
            "Connection": "keep-alive",
            # 禁用 Nginx 缓冲（如果有的话）
            "X-Accel-Buffering": "no",
        },
    )