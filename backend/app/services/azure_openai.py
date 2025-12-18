"""Azure OpenAI service for AI chat completions."""

import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from openai import AzureOpenAI, AsyncAzureOpenAI

from app.core.config import get_settings

# Configure logging
logger = logging.getLogger(__name__)


class AzureOpenAIService:
    """Service class for Azure OpenAI operations."""

    def __init__(self) -> None:
        """Initialize the Azure OpenAI service."""
        self.settings = get_settings()
        
        # Log configuration for debugging
        logger.info(f"Initializing Azure OpenAI Service")
        logger.info(f"  Endpoint: {self.settings.azure_openai_endpoint}")
        logger.info(f"  Deployment: {self.settings.azure_openai_deployment_name}")
        logger.info(f"  API Version: {self.settings.azure_openai_api_version}")
        logger.info(f"  API Key (first 8 chars): {self.settings.azure_openai_api_key[:8]}...")
        
        # Sync client for non-streaming operations
        self.client = AzureOpenAI(
            api_key=self.settings.azure_openai_api_key,
            api_version=self.settings.azure_openai_api_version,
            azure_endpoint=self.settings.azure_openai_endpoint,
        )
        
        # Async client for streaming operations
        self.async_client = AsyncAzureOpenAI(
            api_key=self.settings.azure_openai_api_key,
            api_version=self.settings.azure_openai_api_version,
            azure_endpoint=self.settings.azure_openai_endpoint,
        )
        
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
        Build the messages array for the chat completion.
        
        Args:
            system_prompt: The system prompt to set the AI's behavior
            history: Previous messages in the conversation
            user_message: The current user message
            attachments: Optional list of attachments (images)
        
        Returns:
            List of message objects for the API call
        """
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]

        # Add conversation history
        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"],
            })

        # Build user message content
        if attachments:
            # Multi-modal message with images
            content: List[Dict[str, Any]] = [{"type": "text", "text": user_message}]
            
            for attachment in attachments:
                if attachment.get("type") == "image":
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": attachment["url"],
                            "detail": "auto",
                        },
                    })
            
            messages.append({"role": "user", "content": content})
        else:
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
        Generate a chat completion (non-streaming).
        
        Args:
            system_prompt: The system prompt
            history: Previous messages
            user_message: Current user message
            attachments: Optional attachments
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        
        Returns:
            Dict containing the response content and token usage
        """
        messages = self._build_messages(system_prompt, history, user_message, attachments)

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

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
        Generate a concise, semantic title for a conversation based on the first user message.
        
        Args:
            user_message: The first user message in the conversation
            max_length: Maximum number of characters for the title
        
        Returns:
            A short, descriptive title for the conversation
        """
        prompt = f"""请根据以下用户输入生成一个简短的对话标题。要求：
1. 标题长度在5-15个字之间
2. 不要使用标点符号
3. 简洁准确地概括用户想讨论的主题
4. 直接返回标题，不要有任何其他内容

用户输入：{user_message[:500]}"""  # Limit input length

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "你是一个标题生成助手，只输出简短的标题，不要有任何解释。"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=50,
                temperature=0.3,  # Lower temperature for more focused output
            )
            
            content = response.choices[0].message.content
            title = content.strip() if content else "新对话"
            # Remove any quotes or extra punctuation
            title = title.strip('"\'""''')
            # Ensure title is not too long
            if len(title) > max_length:
                title = title[:max_length]
            
            return title if title else "新对话"
            
        except Exception as e:
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
        Generate a streaming chat completion using async client for true streaming.
        
        Args:
            system_prompt: The system prompt
            history: Previous messages
            user_message: Current user message
            attachments: Optional attachments
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        
        Yields:
            Dict with delta content or finish signal
        """
        messages = self._build_messages(system_prompt, history, user_message, attachments)
        
        logger.info(f"Starting streaming chat completion (async)")
        logger.info(f"  Deployment: {self.deployment_name}")
        logger.info(f"  Messages count: {len(messages)}")
        logger.info(f"  Max tokens: {max_tokens}")
        logger.info(f"  Temperature: {temperature}")

        try:
            # Use async client for true async streaming
            stream = await self.async_client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )
            logger.info("Async stream created successfully, iterating chunks...")

            # Use async for to properly yield chunks without blocking
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    finish_reason = chunk.choices[0].finish_reason

                    if delta.content:
                        yield {
                            "type": "content_delta",
                            "delta": delta.content,
                        }

                    if finish_reason:
                        logger.info(f"Stream finished with reason: {finish_reason}")
                        yield {
                            "type": "finish",
                            "finish_reason": finish_reason,
                        }
        except Exception as e:
            logger.error(f"Azure OpenAI API error: {type(e).__name__}: {str(e)}")
            logger.error(f"  Endpoint used: {self.settings.azure_openai_endpoint}")
            logger.error(f"  Deployment used: {self.deployment_name}")
            raise


# Singleton instance
_openai_service: Optional[AzureOpenAIService] = None


def get_openai_service() -> AzureOpenAIService:
    """Get or create the Azure OpenAI service instance."""
    global _openai_service
    
    if _openai_service is None:
        _openai_service = AzureOpenAIService()
    
    return _openai_service