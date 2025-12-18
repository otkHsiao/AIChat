#!/usr/bin/env python3
"""
用户删除脚本。

本脚本用于从 Azure Cosmos DB 中删除用户，是一个独立的命令行工具。
删除用户时会同时删除该用户的所有对话和消息数据（级联删除）。

⚠️ 警告：此操作不可逆！删除后数据无法恢复。

使用场景：
1. 删除测试用户
2. 用户账户注销
3. 清理无效账户
4. 数据合规性要求（如 GDPR 删除请求）

使用方法：
    # 方式1：按邮箱删除用户
    python delete_user.py --email user@example.com
    
    # 方式2：按 ID 删除用户
    python delete_user.py --id user-uuid-here
    
    # 方式3：修改脚本底部的参数后运行
    asyncio.run(delete_user_by_email("user@example.com"))

删除流程：
┌─────────────────────────────────────────────────────────────────────────┐
│                         用户删除流程（级联删除）                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐                                                    │
│  │  delete_user.py  │                                                    │
│  └────────┬─────────┘                                                    │
│           │                                                               │
│           ▼                                                               │
│  ┌────────────────────────────────────────────────────────┐             │
│  │  1. 验证用户存在                                        │             │
│  │     └─> get_user_by_email() 或 get_user_by_id()        │             │
│  └────────────────────────────────────────────────────────┘             │
│           │                                                               │
│           ▼                                                               │
│  ┌────────────────────────────────────────────────────────┐             │
│  │  2. 获取用户的所有对话                                  │             │
│  │     └─> SELECT * FROM c WHERE c.userId = @userId       │             │
│  └────────────────────────────────────────────────────────┘             │
│           │                                                               │
│           ▼                                                               │
│  ┌────────────────────────────────────────────────────────┐             │
│  │  3. 删除每个对话下的所有消息                            │             │
│  │     └─> DELETE messages WHERE conversationId = ?       │             │
│  └────────────────────────────────────────────────────────┘             │
│           │                                                               │
│           ▼                                                               │
│  ┌────────────────────────────────────────────────────────┐             │
│  │  4. 删除所有对话记录                                    │             │
│  │     └─> DELETE conversations WHERE userId = ?          │             │
│  └────────────────────────────────────────────────────────┘             │
│           │                                                               │
│           ▼                                                               │
│  ┌────────────────────────────────────────────────────────┐             │
│  │  5. 删除用户记录                                        │             │
│  │     └─> DELETE user WHERE id = ?                       │             │
│  └────────────────────────────────────────────────────────┘             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

注意事项：
1. 运行前需要设置环境变量（Cosmos DB 连接信息）
2. 删除操作不可逆，请确认后再执行
3. 删除会级联到对话和消息，确保这是预期行为
4. 建议在删除前先使用 list_users.py 确认用户信息
"""

import asyncio
import sys
import os
import argparse

# ============================================================================
# 路径设置
# ============================================================================

# 获取 backend 目录路径（脚本所在目录的父目录）
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 将 backend 目录添加到 Python 路径
sys.path.insert(0, BACKEND_DIR)

# 切换工作目录到 backend，确保能找到 .env 文件
os.chdir(BACKEND_DIR)

# 加载 .env 文件中的环境变量
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BACKEND_DIR, ".env"))
    load_dotenv(os.path.join(BACKEND_DIR, ".env.local"), override=True)
except ImportError:
    # 如果没有安装 python-dotenv，依赖 pydantic-settings 自动加载
    pass

from typing import Optional, Dict, Any

# 导入数据库服务
from app.services.cosmos_db import CosmosDBService


# ============================================================================
# 用户删除函数
# ============================================================================

async def delete_user_by_id(user_id: str, confirm: bool = False) -> bool:
    """
    根据用户 ID 删除用户及其所有数据。
    
    执行级联删除：
    1. 删除用户的所有消息
    2. 删除用户的所有对话
    3. 删除用户记录
    
    Args:
        user_id: 用户 ID (UUID)
        confirm: 是否跳过确认提示（脚本模式使用）
        
    Returns:
        bool: 删除成功返回 True，失败返回 False
        
    Example:
        >>> success = asyncio.run(delete_user_by_id("user-uuid", confirm=True))
        >>> print("Deleted" if success else "Failed")
    """
    print(f"Preparing to delete user with ID: {user_id}")
    print()
    
    # 初始化 Cosmos DB 连接
    db = CosmosDBService()
    await db.initialize()
    
    # 1. 验证用户存在
    user = await db.get_user_by_id(user_id)
    if not user:
        print(f"Error: User not found with ID: {user_id}")
        return False
    
    # 显示用户信息
    print("User found:")
    print(f"  ID: {user.get('id')}")
    print(f"  Username: {user.get('username')}")
    print(f"  Email: {user.get('email')}")
    print(f"  Created: {user.get('createdAt')}")
    print()
    
    # 确认删除
    if not confirm:
        response = input("⚠️  Are you sure you want to delete this user and ALL their data? (yes/no): ")
        if response.lower() != 'yes':
            print("Deletion cancelled.")
            return False
    
    print()
    print("Starting cascade deletion...")
    
    # 2. 获取用户的所有对话
    conversations_container = db.containers["conversations"]
    conversations = list(conversations_container.query_items(
        query="SELECT * FROM c WHERE c.userId = @userId",
        parameters=[{"name": "@userId", "value": user_id}],
        enable_cross_partition_query=True,
    ))
    
    print(f"Found {len(conversations)} conversations to delete")
    
    # 3. 删除每个对话下的所有消息
    messages_container = db.containers["messages"]
    total_messages_deleted = 0
    
    for conv in conversations:
        conv_id = conv["id"]
        # 获取该对话的所有消息
        messages = list(messages_container.query_items(
            query="SELECT * FROM c WHERE c.conversationId = @convId",
            parameters=[{"name": "@convId", "value": conv_id}],
            enable_cross_partition_query=True,
        ))
        
        # 删除消息
        for msg in messages:
            messages_container.delete_item(
                item=msg["id"],
                partition_key=conv_id  # 消息的分区键是 conversationId
            )
            total_messages_deleted += 1
        
        print(f"  Deleted {len(messages)} messages from conversation: {conv.get('title', conv_id)}")
    
    print(f"Total messages deleted: {total_messages_deleted}")
    
    # 4. 删除所有对话
    for conv in conversations:
        conversations_container.delete_item(
            item=conv["id"],
            partition_key=user_id  # 对话的分区键是 userId
        )
    
    print(f"Deleted {len(conversations)} conversations")
    
    # 5. 删除用户记录
    users_container = db.containers["users"]
    users_container.delete_item(
        item=user_id,
        partition_key=user_id  # 用户的分区键是 id
    )
    
    print()
    print("=" * 60)
    print(f"✅ User '{user.get('username')}' ({user.get('email')}) has been deleted successfully!")
    print(f"   - {len(conversations)} conversations deleted")
    print(f"   - {total_messages_deleted} messages deleted")
    print("=" * 60)
    
    return True


async def delete_user_by_email(email: str, confirm: bool = False) -> bool:
    """
    根据邮箱删除用户及其所有数据。
    
    先通过邮箱查找用户 ID，然后调用 delete_user_by_id 执行删除。
    
    Args:
        email: 用户邮箱地址
        confirm: 是否跳过确认提示
        
    Returns:
        bool: 删除成功返回 True，失败返回 False
    """
    print(f"Searching for user with email: {email}")
    print()
    
    # 初始化 Cosmos DB 连接
    db = CosmosDBService()
    await db.initialize()
    
    # 查找用户
    user = await db.get_user_by_email(email)
    if not user:
        print(f"Error: User not found with email: {email}")
        return False
    
    # 使用用户 ID 执行删除
    return await delete_user_by_id(user["id"], confirm=confirm)


# ============================================================================
# 命令行参数解析
# ============================================================================

def parse_args():
    """
    解析命令行参数。
    
    支持的参数：
        --email: 按邮箱删除用户
        --id: 按用户 ID 删除用户
        --yes: 跳过确认提示
        
    Returns:
        argparse.Namespace: 解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        description="Delete a user and all their data from Cosmos DB"
    )
    
    # 互斥组：必须指定 email 或 id 其中之一
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "--email",
        type=str,
        help="Delete user by email address"
    )
    group.add_argument(
        "--id",
        type=str,
        help="Delete user by user ID (UUID)"
    )
    
    # 跳过确认提示
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt (use with caution!)"
    )
    
    return parser.parse_args()


# ============================================================================
# 脚本入口
# ============================================================================

if __name__ == "__main__":
    args = parse_args()
    
    if args.email:
        # 按邮箱删除
        asyncio.run(delete_user_by_email(args.email, confirm=args.yes))
    elif args.id:
        # 按 ID 删除
        asyncio.run(delete_user_by_id(args.id, confirm=args.yes))
    else:
        # 没有提供参数时，显示帮助信息
        print("Usage examples:")
        print("  python delete_user.py --email user@example.com")
        print("  python delete_user.py --id user-uuid-here")
        print("  python delete_user.py --email user@example.com --yes")
        print()
        print("For more options, run: python delete_user.py --help")
        print()
        
        # 或者可以硬编码一个用户来删除（取消注释以使用）
        # asyncio.run(delete_user_by_email("test@example.com"))