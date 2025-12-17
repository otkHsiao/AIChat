"""Azure Cosmos DB service for database operations."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app.core.config import get_settings


class CosmosDBService:
    """Service class for Azure Cosmos DB operations."""

    def __init__(self) -> None:
        """Initialize the Cosmos DB service."""
        self.settings = get_settings()
        self.client: Optional[CosmosClient] = None
        self.database = None
        self.containers: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """
        Initialize the Cosmos DB client and containers.
        
        Creates the database and containers if they don't exist.
        """
        self.client = CosmosClient(
            url=self.settings.cosmos_db_endpoint,
            credential=self.settings.cosmos_db_key,
        )

        # Create database if not exists
        self.database = self.client.create_database_if_not_exists(
            id=self.settings.cosmos_db_database_name
        )

        # Create containers
        self.containers["users"] = self.database.create_container_if_not_exists(
            id="users",
            partition_key=PartitionKey(path="/id"),
        )

        self.containers["conversations"] = self.database.create_container_if_not_exists(
            id="conversations",
            partition_key=PartitionKey(path="/userId"),
        )

        self.containers["messages"] = self.database.create_container_if_not_exists(
            id="messages",
            partition_key=PartitionKey(path="/conversationId"),
        )

    def _get_container(self, container_name: str) -> Any:
        """Get a container by name."""
        if container_name not in self.containers:
            raise ValueError(f"Container '{container_name}' not found")
        return self.containers[container_name]

    # ==================== User Operations ====================

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            user_data: User data including email, username, passwordHash
        
        Returns:
            Created user document
        """
        container = self._get_container("users")
        
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        user = {
            "id": user_id,
            "email": user_data["email"],
            "username": user_data["username"],
            "passwordHash": user_data["passwordHash"],
            "createdAt": now,
            "updatedAt": now,
            "settings": {
                "defaultModel": "gpt-4o",
                "theme": "light",
            },
        }
        
        container.create_item(body=user)
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by their ID."""
        container = self._get_container("users")
        
        try:
            return container.read_item(item=user_id, partition_key=user_id)
        except CosmosResourceNotFoundError:
            return None

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get a user by their email address."""
        container = self._get_container("users")
        
        query = "SELECT * FROM c WHERE c.email = @email"
        parameters = [{"name": "@email", "value": email}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True,
        ))
        
        return items[0] if items else None

    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a user's information."""
        container = self._get_container("users")
        
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        user.update(updates)
        user["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        container.replace_item(item=user_id, body=user)
        return user

    # ==================== Conversation Operations ====================

    async def create_conversation(
        self, user_id: str, conversation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new conversation.
        
        Args:
            user_id: The ID of the user creating the conversation
            conversation_data: Conversation data including title, systemPrompt, model
        
        Returns:
            Created conversation document
        """
        container = self._get_container("conversations")
        
        conversation_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        conversation = {
            "id": conversation_id,
            "userId": user_id,
            "title": conversation_data.get("title", "新对话"),
            "systemPrompt": conversation_data.get("systemPrompt", "你是一个有帮助的 AI 助手。"),
            "model": conversation_data.get("model", "gpt-4o"),
            "messageCount": 0,
            "createdAt": now,
            "updatedAt": now,
        }
        
        container.create_item(body=conversation)
        return conversation

    async def get_conversation(
        self, conversation_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a conversation by ID, ensuring it belongs to the user."""
        container = self._get_container("conversations")
        
        try:
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
        """Get all conversations for a user, sorted by updatedAt descending."""
        container = self._get_container("conversations")
        
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
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False,
        ))
        
        return items

    async def update_conversation(
        self, conversation_id: str, user_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a conversation."""
        container = self._get_container("conversations")
        
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None
        
        allowed_updates = {"title", "systemPrompt", "model", "messageCount"}
        for key, value in updates.items():
            if key in allowed_updates:
                conversation[key] = value
        
        conversation["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        container.replace_item(item=conversation_id, body=conversation)
        return conversation

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation and all its messages."""
        container = self._get_container("conversations")
        
        try:
            container.delete_item(item=conversation_id, partition_key=user_id)
            
            # Delete all messages in the conversation
            await self.delete_messages_by_conversation(conversation_id)
            
            return True
        except CosmosResourceNotFoundError:
            return False

    # ==================== Message Operations ====================

    async def create_message(
        self, conversation_id: str, message_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new message in a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            message_data: Message data including role, content, attachments
        
        Returns:
            Created message document
        """
        container = self._get_container("messages")
        
        message_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        message = {
            "id": message_id,
            "conversationId": conversation_id,
            "role": message_data["role"],
            "content": message_data["content"],
            "attachments": message_data.get("attachments", []),
            "tokens": message_data.get("tokens"),
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
        """Get messages for a conversation, sorted by createdAt ascending."""
        container = self._get_container("messages")
        
        if before_id:
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
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False,
        ))
        
        return items

    async def delete_messages_by_conversation(self, conversation_id: str) -> int:
        """Delete all messages in a conversation."""
        container = self._get_container("messages")
        
        query = "SELECT c.id FROM c WHERE c.conversationId = @conversationId"
        parameters = [{"name": "@conversationId", "value": conversation_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False,
        ))
        
        count = 0
        for item in items:
            container.delete_item(item=item["id"], partition_key=conversation_id)
            count += 1
        
        return count

    async def count_conversations_by_user(self, user_id: str) -> int:
        """Count total conversations for a user."""
        container = self._get_container("conversations")
        
        query = "SELECT VALUE COUNT(1) FROM c WHERE c.userId = @userId"
        parameters = [{"name": "@userId", "value": user_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False,
        ))
        
        return items[0] if items else 0