"""
Azure OpenAI 服务模块 - AI 聊天补全功能。

本模块封装了与 Azure OpenAI 服务的所有交互，提供：
1. 聊天补全（Chat Completion）- 生成 AI 回复
2. 流式响应（Streaming）- 实时输出 AI 回复
3. 多模态支持（Vision）- 处理图片输入
4. 对话标题生成 - 自动为对话生成语义化标题

Azure OpenAI vs OpenAI：
- Azure OpenAI 是微软在 Azure 上托管的 OpenAI 服务
- 提供企业级安全、合规和区域数据驻留
- API 格式与 OpenAI 兼容，但需要使用 Azure 端点和部署名称

消息格式（Chat Completion API）：
[
    {"role": "system", "content": "系统提示词，设定 AI 行为"},
    {"role": "user", "content": "用户消息"},
    {"role": "assistant", "content": "AI 回复"},
    {"role": "user", "content": "用户后续消息"},
    ...
]

多模态消息格式（带图片）：
{
    "role": "user",
    "content": [
        {"type": "text", "text": "描述这张图片"},
        {"type": "image_url", "image_url": {"url": "https://...", "detail": "auto"}}
    ]
}

流式响应（SSE）：
- 服务器发送事件（Server-Sent Events）
- 实时将 AI 生成的内容发送给客户端
- 提供更好的用户体验，无需等待完整响应
"""

# logging: Python 标准库，提供日志记录功能
import logging

# Any: 任意类型注解
# AsyncGenerator: 异步生成器类型注解，用于流式响应
# Dict: 字典类型注解
# List: 列表类型注解
# Optional: 可选类型注解
from typing import Any, AsyncGenerator, Dict, List, Optional

# AzureOpenAI: Azure OpenAI 同步客户端，用于非流式请求
# AsyncAzureOpenAI: Azure OpenAI 异步客户端，用于流式响应
from openai import AzureOpenAI, AsyncAzureOpenAI

# get_settings: 获取应用配置的函数
from app.core.config import get_settings

# 配置日志记录器
# 使用模块名作为 logger 名称，便于日志分类和过滤
logger = logging.getLogger(__name__)


class AzureOpenAIService:
    """
    Azure OpenAI 服务类。
    
    封装与 Azure OpenAI API 的所有交互，提供同步和异步两种客户端：
    - 同步客户端：用于简单的请求-响应场景
    - 异步客户端：用于流式响应，支持真正的异步迭代
    
    设计模式：
    - 使用单例模式（通过 get_openai_service 函数）
    - 延迟初始化客户端
    """

    def __init__(self) -> None:
        """
        初始化 Azure OpenAI 服务。
        
        创建同步和异步两个客户端实例，用于不同的使用场景。
        初始化时会记录配置信息用于调试。
        """
        self.settings = get_settings()
        
        # 记录配置信息用于调试（注意：只记录 API Key 的前 8 个字符）
        logger.info(f"Initializing Azure OpenAI Service")
        logger.info(f"  Endpoint: {self.settings.azure_openai_endpoint}")
        logger.info(f"  Deployment: {self.settings.azure_openai_deployment_name}")
        logger.info(f"  API Version: {self.settings.azure_openai_api_version}")
        logger.info(f"  API Key (first 8 chars): {self.settings.azure_openai_api_key[:8]}...")
        
        # ========== 同步客户端 ==========
        # 用于非流式操作，如生成标题、简单对话
        self.client = AzureOpenAI(
            api_key=self.settings.azure_openai_api_key,
            api_version=self.settings.azure_openai_api_version,
            azure_endpoint=self.settings.azure_openai_endpoint,
        )
        
        # ========== 异步客户端 ==========
        # 用于流式响应，支持 async for 迭代
        # 这对于 SSE（服务器发送事件）场景至关重要
        self.async_client = AsyncAzureOpenAI(
            api_key=self.settings.azure_openai_api_key,
            api_version=self.settings.azure_openai_api_version,
            azure_endpoint=self.settings.azure_openai_endpoint,
        )
        
        # 保存部署名称供后续使用
        self.deployment_name = self.settings.azure_openai_deployment_name
        logger.info(f"Azure OpenAI client initialized successfully")

    def _build_messages(
        self,
        system_prompt: str,
        history: List[Dict[str, Any]],
        user_message: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        构建聊天补全 API 的消息数组。
        
        根据 OpenAI 的消息格式规范，构建包含系统提示、历史对话和当前用户消息的数组。
        如果有图片附件，会构建多模态消息格式。
        
        消息顺序：
        1. 系统提示（设定 AI 的行为和角色）
        2. 历史消息（提供对话上下文）
        3. 当前用户消息（可能包含图片）
        
        Args:
            system_prompt: 系统提示词，用于设定 AI 的行为
            history: 历史对话消息列表
            user_message: 当前用户消息内容
            attachments: 可选的附件列表（目前支持图片）
            
        Returns:
            List[Dict]: 符合 OpenAI API 规范的消息数组
            
        多模态支持：
        - 当存在图片附件时，用户消息会被转换为多模态格式
        - 图片通过 URL 传递给 API（需要是可公开访问的 URL）
        - detail 参数控制图片分析的详细程度
        """
        # 初始化消息列表，首先添加系统提示
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]

        # 添加历史对话记录
        # 这为 AI 提供对话上下文，使其能够进行连贯的多轮对话
        for msg in history:
            messages.append({
                "role": msg["role"],      # "user" 或 "assistant"
                "content": msg["content"],
            })

        # 构建当前用户消息
        if attachments:
            # 多模态消息格式（带图片）
            # content 是一个数组，包含文本和图片
            content: List[Dict[str, Any]] = [{"type": "text", "text": user_message}]
            
            for attachment in attachments:
                if attachment.get("type") == "image":
                    # 添加图片到消息内容
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": attachment["url"],
                            # detail 可以是 "auto", "low", "high"
                            # "auto" 让模型自动选择
                            "detail": "auto",
                        },
                    })
            
            messages.append({"role": "user", "content": content})
        else:
            # 纯文本消息格式
            messages.append({"role": "user", "content": user_message})

        return messages

    async def chat_completion(
        self,
        system_prompt: str,
        history: List[Dict[str, Any]],
        user_message: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        生成聊天补全（非流式）。
        
        向 Azure OpenAI API 发送请求并等待完整响应。
        适用于不需要实时显示的场景。
        
        Args:
            system_prompt: 系统提示词
            history: 历史对话消息
            user_message: 当前用户消息
            attachments: 可选的附件（图片等）
            max_tokens: 生成的最大令牌数（默认 4096）
            temperature: 采样温度（0-2，越高越随机，默认 0.7）
            
        Returns:
            Dict: 包含以下字段：
                - content: AI 生成的回复内容
                - tokens: 令牌使用统计 {"input": N, "output": M}
                - finish_reason: 完成原因（"stop", "length" 等）
                
        Temperature 说明：
        - 0: 几乎确定性的输出，适合事实性问答
        - 0.7: 平衡创造性和一致性
        - 1.0+: 更具创造性，适合创意写作
        """
        # 构建消息数组
        messages = self._build_messages(system_prompt, history, user_message, attachments)

        # 调用 Azure OpenAI API
        response = self.client.chat.completions.create(
            model=self.deployment_name,  # Azure 中使用部署名称
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # 解析并返回响应
        return {
            "content": response.choices[0].message.content,
            "tokens": {
                "input": response.usage.prompt_tokens if response.usage else 0,
                "output": response.usage.completion_tokens if response.usage else 0,
            },
            "finish_reason": response.choices[0].finish_reason,
        }

    async def generate_conversation_title(
        self,
        user_message: str,
        max_length: int = 20,
    ) -> str:
        """
        根据第一条用户消息生成对话标题。
        
        使用 AI 分析用户的输入，生成简洁、语义化的对话标题。
        这比简单截取用户消息更智能。
        
        Args:
            user_message: 第一条用户消息内容
            max_length: 标题最大字符数（默认 20）
            
        Returns:
            str: 生成的对话标题，失败时返回"新对话"
            
        生成策略：
        - 使用较低的 temperature（0.3）确保输出稳定
        - 限制输入长度避免超出令牌限制
        - 清理输出中的引号和标点
        """
        # 构建提示词，详细说明生成要求
        prompt = f"""请根据以下用户输入生成一个简短的对话标题。要求：
1. 标题长度在5-15个字之间
2. 不要使用标点符号
3. 简洁准确地概括用户想讨论的主题
4. 直接返回标题，不要有任何其他内容

用户输入：{user_message[:500]}"""  # 限制输入长度，避免令牌超限

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    # 简洁的系统提示，专注于标题生成任务
                    {"role": "system", "content": "你是一个标题生成助手，只输出简短的标题，不要有任何解释。"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=50,       # 标题不需要太多令牌
                temperature=0.3,     # 较低的温度，确保输出一致
            )
            
            # 提取并清理标题
            content = response.choices[0].message.content
            title = content.strip() if content else "新对话"
            
            # 移除可能存在的引号
            title = title.strip('"\'""''')
            
            # 确保标题不超过最大长度
            if len(title) > max_length:
                title = title[:max_length]
            
            return title if title else "新对话"
            
        except Exception as e:
            # 标题生成失败不应影响主流程
            logger.warning(f"Failed to generate title: {e}")
            return "新对话"

    async def chat_completion_stream(
        self,
        system_prompt: str,
        history: List[Dict[str, Any]],
        user_message: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        生成流式聊天补全。
        
        使用异步客户端实现真正的流式响应，每当 AI 生成一段内容，
        就立即通过 yield 返回给调用者。这样前端可以实时显示 AI 的回复，
        无需等待完整响应。
        
        流式响应的工作原理：
        1. 客户端发起请求时设置 stream=True
        2. 服务器逐块返回生成的内容
        3. 本函数使用 async for 迭代这些块
        4. 每个块被包装成事件对象 yield 给调用者
        
        事件类型：
        - content_delta: 包含新生成的文本片段
        - finish: 表示生成完成，包含完成原因
        
        Args:
            system_prompt: 系统提示词
            history: 历史对话消息
            user_message: 当前用户消息
            attachments: 可选的附件（图片等）
            max_tokens: 生成的最大令牌数
            temperature: 采样温度
            
        Yields:
            Dict: 事件对象，格式如下：
                - {"type": "content_delta", "delta": "文本片段"}
                - {"type": "finish", "finish_reason": "stop"}
                
        使用示例：
            async for chunk in service.chat_completion_stream(...):
                if chunk["type"] == "content_delta":
                    print(chunk["delta"], end="", flush=True)
                elif chunk["type"] == "finish":
                    print("\\n完成！")
                    
        SSE 集成：
        在 FastAPI 中，这个生成器通常用于构建 SSE 响应：
        
            async def generate():
                async for chunk in service.chat_completion_stream(...):
                    yield f"data: {json.dumps(chunk)}\\n\\n"
            return StreamingResponse(generate(), media_type="text/event-stream")
        """
        # 构建消息数组
        messages = self._build_messages(system_prompt, history, user_message, attachments)
        
        # 记录请求信息用于调试
        logger.info(f"Starting streaming chat completion (async)")
        logger.info(f"  Deployment: {self.deployment_name}")
        logger.info(f"  Messages count: {len(messages)}")
        logger.info(f"  Max tokens: {max_tokens}")
        logger.info(f"  Temperature: {temperature}")

        try:
            # ========== 创建流式响应 ==========
            # 使用异步客户端和 stream=True 参数
            # 返回的 stream 是一个异步迭代器
            stream = await self.async_client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,  # 关键参数：启用流式模式
            )
            logger.info("Async stream created successfully, iterating chunks...")

            # ========== 迭代处理流式响应 ==========
            # 使用 async for 确保不阻塞事件循环
            async for chunk in stream:
                # 检查是否有有效的响应选择
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    finish_reason = chunk.choices[0].finish_reason

                    # 处理内容增量
                    # delta.content 包含新生成的文本片段
                    if delta.content:
                        yield {
                            "type": "content_delta",
                            "delta": delta.content,
                        }

                    # 处理完成信号
                    # finish_reason 可能是 "stop"（正常结束）或 "length"（达到最大令牌数）
                    if finish_reason:
                        logger.info(f"Stream finished with reason: {finish_reason}")
                        yield {
                            "type": "finish",
                            "finish_reason": finish_reason,
                        }
                        
        except Exception as e:
            # 记录详细错误信息用于调试
            logger.error(f"Azure OpenAI API error: {type(e).__name__}: {str(e)}")
            logger.error(f"  Endpoint used: {self.settings.azure_openai_endpoint}")
            logger.error(f"  Deployment used: {self.deployment_name}")
            # 重新抛出异常，让调用者处理
            raise


# ============================================================================
# 单例模式实现
# ============================================================================

# 全局服务实例
_openai_service: Optional[AzureOpenAIService] = None


def get_openai_service() -> AzureOpenAIService:
    """
    获取 Azure OpenAI 服务的单例实例。
    
    使用单例模式确保：
    1. 整个应用共享同一个服务实例
    2. 只初始化一次客户端连接
    3. 避免重复创建资源
    
    Returns:
        AzureOpenAIService: 服务实例
        
    使用方式：
        from app.services.azure_openai import get_openai_service
        
        service = get_openai_service()
        response = await service.chat_completion(...)
    """
    global _openai_service
    
    if _openai_service is None:
        _openai_service = AzureOpenAIService()
    
    return _openai_service