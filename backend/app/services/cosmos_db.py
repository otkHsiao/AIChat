"""
Azure Cosmos DB 数据库服务模块。

本模块封装了与 Azure Cosmos DB NoSQL 数据库的所有交互操作。
Cosmos DB 是一个全球分布式、多模型数据库服务，本应用使用其 NoSQL API。

数据模型设计：
┌─────────────────────────────────────────────────────────────────┐
│ users 容器                                                       │
│ 分区键: /id                                                      │
│ 存储: 用户账户信息                                                │
├─────────────────────────────────────────────────────────────────┤
│ {                                                                │
│   "id": "uuid",                                                  │
│   "email": "user@example.com",                                  │
│   "username": "用户名",                                          │
│   "passwordHash": "bcrypt哈希",                                  │
│   "settings": { "defaultModel": "gpt-4o", "theme": "light" },   │
│   "createdAt": "ISO时间戳",                                      │
│   "updatedAt": "ISO时间戳"                                       │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ conversations 容器                                               │
│ 分区键: /userId (按用户分区，查询用户对话效率高)                   │
├─────────────────────────────────────────────────────────────────┤
│ {                                                                │
│   "id": "uuid",                                                  │
│   "userId": "用户ID",                                            │
│   "title": "对话标题",                                           │
│   "systemPrompt": "系统提示词",                                   │
│   "model": "gpt-4o",                                             │
│   "messageCount": 10,                                            │
│   "createdAt": "ISO时间戳",                                      │
│   "updatedAt": "ISO时间戳"                                       │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ messages 容器                                                    │
│ 分区键: /conversationId (按对话分区，查询对话消息效率高)           │
├─────────────────────────────────────────────────────────────────┤
│ {                                                                │
│   "id": "uuid",                                                  │
│   "conversationId": "对话ID",                                    │
│   "role": "user|assistant",                                      │
│   "content": "消息内容",                                          │
│   "attachments": [...],                                          │
│   "tokens": { "input": 100, "output": 200 },                    │
│   "createdAt": "ISO时间戳"                                       │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘

分区键设计原则：
1. 选择查询最频繁的字段作为分区键
2. 确保分区大小均匀分布
3. 同一分区内的查询效率最高
"""

# Any: 任意类型注解
# Dict: 字典类型注解
# List: 列表类型注解
# Optional: 可选类型注解
from typing import Any, Dict, List, Optional, cast

# datetime: 日期时间类，用于处理时间戳
# timezone: 时区类，用于 UTC 时间处理
from datetime import datetime, timezone

# uuid: Python 标准库，用于生成唯一的 ID（用户 ID、对话 ID、消息 ID）
import uuid

# CosmosClient: Azure Cosmos DB 客户端类
# PartitionKey: 分区键定义类，用于创建容器时指定分区键
from azure.cosmos import ContainerProxy, CosmosClient, PartitionKey

# CosmosResourceNotFoundError: Cosmos DB 资源未找到异常（如用户不存在）
from azure.cosmos.exceptions import CosmosResourceNotFoundError

# get_settings: 获取应用配置的函数
from app.core.config import get_settings


class CosmosDBService:
    """
    Azure Cosmos DB 服务类。
    
    封装所有数据库操作，提供用户、对话、消息的 CRUD 功能。
    使用单例模式，通过依赖注入获取实例。
    
    使用方式：
        db = await get_cosmos_db()
        user = await db.get_user_by_id(user_id)
    
    设计模式：
    - Repository 模式：将数据访问逻辑封装在服务类中
    - 异步支持：所有公共方法都是异步的，支持并发
    """

    def __init__(self) -> None:
        """
        初始化 Cosmos DB 服务。
        
        注意：此时只是创建服务实例，还未建立数据库连接。
        需要调用 initialize() 方法来建立连接。
        """
        self.settings = get_settings()
        # Cosmos DB 客户端实例
        self.client: Optional[CosmosClient] = None
        # 数据库实例
        self.database = None
        # 容器（集合）字典，键为容器名称
        self.containers: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """
        初始化 Cosmos DB 客户端和容器。
        
        此方法执行以下操作：
        1. 创建 Cosmos DB 客户端连接
        2. 创建数据库（如果不存在）
        3. 创建所有必需的容器（如果不存在）
        
        幂等性：
        - 使用 create_*_if_not_exists 方法确保可重复执行
        - 已存在的资源不会被重新创建或修改
        
        Note:
            应该在应用启动时调用一次，通常在依赖注入中处理
        """
        # 创建 Cosmos DB 客户端
        # 使用端点 URL 和主密钥进行认证
        self.client = CosmosClient(
            url=self.settings.cosmos_db_endpoint,
            credential=self.settings.cosmos_db_key,
        )

        # 创建数据库（如果不存在）
        # 默认吞吐量由 Azure 门户中的设置决定
        self.database = self.client.create_database_if_not_exists(
            id=self.settings.cosmos_db_database_name
        )

        # ========== 创建容器 ==========
        
        # 用户容器
        # 分区键使用 /id，因为用户查询通常按 ID 进行
        self.containers["users"] = self.database.create_container_if_not_exists(
            id="users",
            partition_key=PartitionKey(path="/id"),
        )

        # 对话容器
        # 分区键使用 /userId，因为最常见的查询是获取某用户的所有对话
        self.containers["conversations"] = self.database.create_container_if_not_exists(
            id="conversations",
            partition_key=PartitionKey(path="/userId"),
        )

        # 消息容器
        # 分区键使用 /conversationId，因为最常见的查询是获取某对话的所有消息
        self.containers["messages"] = self.database.create_container_if_not_exists(
            id="messages",
            partition_key=PartitionKey(path="/conversationId"),
        )

    def _get_container(self, container_name: str) -> ContainerProxy:
        """
        根据名称获取容器实例。
        
        这是一个内部辅助方法，用于获取容器引用。
        
        Args:
            container_name: 容器名称（"users"、"conversations" 或 "messages"）
            
        Returns:
            容器实例
            
        Raises:
            ValueError: 如果容器名称无效
        """
        if container_name not in self.containers:
            raise ValueError(f"Container '{container_name}' not found")
        return self.containers[container_name]

    # ========================================================================
    # 用户操作 (User Operations)
    # ========================================================================

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建新用户。
        
        生成唯一的用户 ID，设置默认配置，并保存到数据库。
        
        Args:
            user_data: 用户数据字典，必须包含：
                - email: 邮箱地址
                - username: 用户名
                - passwordHash: 密码哈希值（使用 bcrypt）
                
        Returns:
            Dict: 创建的用户文档，包含生成的 ID 和时间戳
            
        Example:
            user = await db.create_user({
                "email": "user@example.com",
                "username": "testuser",
                "passwordHash": get_password_hash("password123")
            })
        """
        container = self._get_container("users")
        
        # 生成唯一的用户 ID
        user_id = str(uuid.uuid4())
        # 使用 UTC 时间戳，ISO 8601 格式
        now = datetime.now(timezone.utc).isoformat()
        
        # 构建完整的用户文档
        user = {
            "id": user_id,
            "email": user_data["email"],
            "username": user_data["username"],
            "passwordHash": user_data["passwordHash"],
            "createdAt": now,
            "updatedAt": now,
            # 用户默认设置
            "settings": {
                "defaultModel": "gpt-4o",  # 默认使用的 AI 模型
                "theme": "light",           # 默认主题
            },
        }
        
        # 保存到 Cosmos DB
        container.create_item(body=user)
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        根据用户 ID 获取用户信息。
        
        由于分区键是 /id，这是一个高效的点读操作。
        时间复杂度：O(1)，消耗的 RU 最少。
        
        Args:
            user_id: 用户 ID
            
        Returns:
            Optional[Dict]: 用户文档，如果不存在则返回 None
        """
        container = self._get_container("users")
        
        try:
            # 使用点读操作（最高效）
            # partition_key 必须与 item 匹配
            return container.read_item(item=user_id, partition_key=user_id)
        except CosmosResourceNotFoundError:
            # 用户不存在
            return None

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        根据邮箱地址获取用户信息。
        
        由于邮箱不是分区键，需要跨分区查询。
        这比按 ID 查询效率低，但邮箱在用户表中应该是唯一的。
        
        Args:
            email: 用户邮箱地址
            
        Returns:
            Optional[Dict]: 用户文档，如果不存在则返回 None
            
        Note:
            enable_cross_partition_query=True 允许跨所有分区查询
            生产环境中可以考虑为 email 字段建立索引
        """
        container = self._get_container("users")
        
        # 使用参数化查询防止 SQL 注入
        query = "SELECT * FROM c WHERE c.email = @email"
        parameters: list[dict[str, object]] = [{"name": "@email", "value": email}]
        
        # 执行跨分区查询
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True,  # 必须启用跨分区查询
        ))
        
        # 返回第一个匹配的用户（邮箱应该是唯一的）
        return items[0] if items else None

    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        更新用户信息。
        
        使用读取-修改-写入模式更新用户文档。
        
        Args:
            user_id: 用户 ID
            updates: 要更新的字段字典
            
        Returns:
            Optional[Dict]: 更新后的用户文档，如果用户不存在则返回 None
            
        Note:
            Cosmos DB 不支持部分更新（Patch），需要替换整个文档
            这在高并发场景下可能导致冲突，可以使用乐观锁处理
        """
        container = self._get_container("users")
        
        # 先获取现有用户
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        # 更新字段
        user.update(updates)
        # 更新修改时间
        user["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        # 替换整个文档
        container.replace_item(item=user_id, body=user)
        return user

    # ========================================================================
    # 对话操作 (Conversation Operations)
    # ========================================================================

    async def create_conversation(
        self, user_id: str, conversation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建新对话。
        
        每个对话都属于一个用户，包含标题、系统提示词和模型设置。
        对话创建后，用户可以在其中发送消息与 AI 交互。
        
        Args:
            user_id: 创建对话的用户 ID
            conversation_data: 对话配置，可包含：
                - title: 对话标题（默认"新对话"）
                - systemPrompt: 系统提示词（设定 AI 的行为）
                - model: 使用的 AI 模型（默认"gpt-4o"）
                
        Returns:
            Dict: 创建的对话文档
            
        Example:
            conversation = await db.create_conversation(
                user_id="xxx",
                conversation_data={
                    "title": "Python 学习",
                    "systemPrompt": "你是一个 Python 编程导师"
                }
            )
        """
        container = self._get_container("conversations")
        
        # 生成唯一的对话 ID
        conversation_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        # 构建对话文档，使用默认值填充可选字段
        conversation = {
            "id": conversation_id,
            "userId": user_id,  # 分区键，用于高效查询用户的对话
            "title": conversation_data.get("title", "新对话"),
            "systemPrompt": conversation_data.get("systemPrompt", "你是一个有帮助的 AI 助手。"),
            "model": conversation_data.get("model", "gpt-4o"),
            "messageCount": 0,  # 消息计数，用于快速显示对话信息
            "createdAt": now,
            "updatedAt": now,
        }
        
        container.create_item(body=conversation)
        return conversation

    async def get_conversation(
        self, conversation_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取对话，同时验证所有权。
        
        安全考虑：
        - 必须同时提供对话 ID 和用户 ID
        - 利用分区键确保用户只能访问自己的对话
        - 这是一个高效的点读操作
        
        Args:
            conversation_id: 对话 ID
            user_id: 用户 ID（分区键）
            
        Returns:
            Optional[Dict]: 对话文档，如果不存在或不属于该用户则返回 None
        """
        container = self._get_container("conversations")
        
        try:
            # 使用点读操作，partition_key 确保安全性和效率
            conversation = container.read_item(
                item=conversation_id, partition_key=user_id
            )
            return conversation
        except CosmosResourceNotFoundError:
            return None

    async def get_conversations_by_user(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        获取用户的所有对话列表。
        
        返回按更新时间倒序排列的对话列表，最近更新的排在前面。
        支持分页，适用于对话列表 UI。
        
        Args:
            user_id: 用户 ID
            limit: 返回的最大对话数（默认20，用于分页）
            offset: 跳过的对话数（默认0，用于分页）
            
        Returns:
            List[Dict]: 对话文档列表
            
        Note:
            enable_cross_partition_query=False 因为我们按分区键查询
            这确保查询只在用户的分区内执行，效率更高
        """
        container = self._get_container("conversations")
        
        # 使用 SQL 查询获取对话列表
        # ORDER BY updatedAt DESC 确保最近活跃的对话排在前面
        query = """
            SELECT * FROM c
            WHERE c.userId = @userId
            ORDER BY c.updatedAt DESC
            OFFSET @offset LIMIT @limit
        """
        parameters = [
            {"name": "@userId", "value": user_id},
            {"name": "@offset", "value": offset},
            {"name": "@limit", "value": limit},
        ]
        
        # 不需要跨分区查询，因为按分区键（userId）过滤
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False,
        ))
        
        return items

    async def update_conversation(
        self, conversation_id: str, user_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        更新对话信息。
        
        使用白名单机制只允许更新特定字段，防止恶意修改。
        
        Args:
            conversation_id: 对话 ID
            user_id: 用户 ID（用于验证所有权）
            updates: 要更新的字段字典
            
        Returns:
            Optional[Dict]: 更新后的对话文档，如果不存在则返回 None
            
        允许更新的字段：
        - title: 对话标题
        - systemPrompt: 系统提示词
        - model: 使用的 AI 模型
        - messageCount: 消息计数
        """
        container = self._get_container("conversations")
        
        # 先获取现有对话（同时验证所有权）
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None
        
        # 白名单机制：只允许更新指定字段
        allowed_updates = {"title", "systemPrompt", "model", "messageCount"}
        for key, value in updates.items():
            if key in allowed_updates:
                conversation[key] = value
        
        # 更新修改时间
        conversation["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        # 替换整个文档
        container.replace_item(item=conversation_id, body=conversation)
        return conversation

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """
        删除对话及其所有消息。
        
        这是一个级联删除操作：
        1. 删除对话文档
        2. 删除该对话下的所有消息
        
        Args:
            conversation_id: 对话 ID
            user_id: 用户 ID（用于验证所有权）
            
        Returns:
            bool: 删除成功返回 True，对话不存在返回 False
            
        Note:
            消息删除是在对话删除后进行的
            如果消息删除失败，可能会产生孤儿消息
            生产环境可考虑使用事务或后台清理任务
        """
        container = self._get_container("conversations")
        
        try:
            # 删除对话文档
            container.delete_item(item=conversation_id, partition_key=user_id)
            
            # 级联删除所有消息
            await self.delete_messages_by_conversation(conversation_id)
            
            return True
        except CosmosResourceNotFoundError:
            return False

    # ========================================================================
    # 消息操作 (Message Operations)
    # ========================================================================

    async def create_message(
        self, conversation_id: str, message_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        在对话中创建新消息。
        
        消息可以是用户消息或 AI 助手的回复。
        支持附件（如图片），用于多模态对话。
        
        Args:
            conversation_id: 对话 ID（分区键）
            message_data: 消息数据，必须包含：
                - role: 消息角色（"user" 或 "assistant"）
                - content: 消息内容
                可选字段：
                - attachments: 附件列表（图片等）
                - tokens: 令牌使用统计
                
        Returns:
            Dict: 创建的消息文档
            
        Example:
            # 创建用户消息
            user_msg = await db.create_message(
                conversation_id="xxx",
                message_data={
                    "role": "user",
                    "content": "你好！",
                    "attachments": []
                }
            )
            
            # 创建 AI 回复
            ai_msg = await db.create_message(
                conversation_id="xxx",
                message_data={
                    "role": "assistant",
                    "content": "你好！有什么我可以帮助的吗？",
                    "tokens": {"input": 10, "output": 15}
                }
            )
        """
        container = self._get_container("messages")
        
        message_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        # 构建消息文档
        message = {
            "id": message_id,
            "conversationId": conversation_id,  # 分区键
            "role": message_data["role"],       # "user" 或 "assistant"
            "content": message_data["content"], # 消息文本内容
            "attachments": message_data.get("attachments", []),  # 附件列表
            "tokens": message_data.get("tokens"),  # 令牌使用统计（用于计费）
            "createdAt": now,
        }
        
        container.create_item(body=message)
        return message

    async def get_messages_by_conversation(
        self,
        conversation_id: str,
        limit: int = 50,
        before_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取对话中的消息历史。
        
        支持两种模式：
        1. 获取最新消息（before_id=None）：按时间正序返回
        2. 加载更多（before_id 指定）：获取指定消息之前的消息
        
        Args:
            conversation_id: 对话 ID
            limit: 返回的最大消息数（默认50）
            before_id: 获取此消息之前的消息（用于"加载更多"功能）
            
        Returns:
            List[Dict]: 消息文档列表
            
        排序说明：
        - 无 before_id：按时间正序（最早的在前）
        - 有 before_id：按时间倒序，然后在前端反转
        """
        container = self._get_container("messages")
        
        if before_id:
            # 加载更多：获取指定消息之前的消息
            # 使用子查询获取参考消息的时间戳
            query = """
                SELECT * FROM c
                WHERE c.conversationId = @conversationId
                AND c.createdAt < (SELECT c2.createdAt FROM c c2 WHERE c2.id = @beforeId)
                ORDER BY c.createdAt DESC
                OFFSET 0 LIMIT @limit
            """
            parameters = [
                {"name": "@conversationId", "value": conversation_id},
                {"name": "@beforeId", "value": before_id},
                {"name": "@limit", "value": limit},
            ]
        else:
            # 获取最新消息：按时间正序
            query = """
                SELECT * FROM c
                WHERE c.conversationId = @conversationId
                ORDER BY c.createdAt ASC
                OFFSET 0 LIMIT @limit
            """
            parameters = [
                {"name": "@conversationId", "value": conversation_id},
                {"name": "@limit", "value": limit},
            ]
        
        # 不需要跨分区查询
        items: list[dict[str, Any]] = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False,
        ))
        
        return items

    async def delete_messages_by_conversation(self, conversation_id: str) -> int:
        """
        删除对话中的所有消息。
        
        通常在删除对话时调用，用于清理关联的消息数据。
        
        Args:
            conversation_id: 对话 ID
            
        Returns:
            int: 删除的消息数量
            
        实现说明：
        1. 首先查询所有消息的 ID
        2. 逐个删除消息
        这种方式在消息量大时可能较慢，
        生产环境可考虑批量删除或后台任务
        """
        container = self._get_container("messages")
        
        # 只查询 ID，减少数据传输
        query = "SELECT c.id FROM c WHERE c.conversationId = @conversationId"
        parameters: list[dict[str, object]] = [{"name": "@conversationId", "value": conversation_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False,
        ))
        
        # 逐个删除消息
        count = 0
        for item in items:
            container.delete_item(item=item["id"], partition_key=conversation_id)
            count += 1
        
        return count

    async def count_conversations_by_user(self, user_id: str) -> int:
        """
        统计用户的对话总数。
        
        用于分页显示时提供总数信息。
        使用 COUNT 聚合函数，效率高于获取所有文档后计数。
        
        Args:
            user_id: 用户 ID
            
        Returns:
            int: 对话总数
            
        Note:
            使用 SELECT VALUE COUNT(1) 直接返回数值，而非文档
        """
        container = self._get_container("conversations")
        
        # 使用 COUNT 聚合函数
        query = "SELECT VALUE COUNT(1) FROM c WHERE c.userId = @userId"
        parameters: list[dict[str, object]] = [{"name": "@userId", "value": user_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False,
        ))
        
        # COUNT 返回单个数值，使用 cast 告知类型检查器 SELECT VALUE 返回的是整数
        return cast(int, items[0]) if items else 0