#!/usr/bin/env python3
"""
用户查询脚本。

本脚本用于查询 Azure Cosmos DB 中的用户信息，是一个独立的命令行工具。
支持列出所有用户或按邮箱/ID 查询特定用户。

使用场景：
1. 查看系统中所有注册用户
2. 验证用户是否存在
3. 获取特定用户的详细信息
4. 运维排查用户相关问题

使用方法：
    # 方式1：列出所有用户
    python list_users.py
    
    # 方式2：按邮箱查询（修改脚本底部的参数）
    asyncio.run(get_user_by_email("user@example.com"))
    
    # 方式3：按 ID 查询（修改脚本底部的参数）
    asyncio.run(get_user_by_id("user-uuid-here"))

输出格式：
┌─────────────────────────────────────────────────────────────────────────┐
│ 用户列表输出示例                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Found 2 users:                                                          │
│  ============================================================           │
│  [1] User: admin                                                         │
│      ID: 550e8400-e29b-41d4-a716-446655440000                            │
│      Email: admin@example.com                                            │
│      Created: 2024-01-01T00:00:00.000Z                                   │
│      Updated: 2024-01-01T00:00:00.000Z                                   │
│  ------------------------------------------------------------           │
│  [2] User: testuser                                                      │
│      ID: 550e8400-e29b-41d4-a716-446655440001                            │
│      Email: test@example.com                                             │
│      Created: 2024-01-02T00:00:00.000Z                                   │
│      Updated: 2024-01-02T00:00:00.000Z                                   │
│  ============================================================           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

注意事项：
1. 运行前需要设置环境变量（Cosmos DB 连接信息）
2. 列出所有用户时会执行跨分区查询，数据量大时可能较慢
3. 密码哈希不会显示在输出中（安全考虑）
"""

import asyncio
import sys
import os

# ============================================================================
# 路径设置
# ============================================================================

# 获取 backend 目录路径（脚本所在目录的父目录）
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 将 backend 目录添加到 Python 路径
# 这样才能导入 app 包中的模块
sys.path.insert(0, BACKEND_DIR)

# 切换工作目录到 backend，确保能找到 .env 文件
os.chdir(BACKEND_DIR)

# 加载 .env 文件中的环境变量
# 使用 python-dotenv 库（如果 pydantic-settings 无法自动加载）
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BACKEND_DIR, ".env"))
    load_dotenv(os.path.join(BACKEND_DIR, ".env.local"), override=True)
except ImportError:
    # 如果没有安装 python-dotenv，依赖 pydantic-settings 自动加载
    pass

from typing import Optional, List, Dict, Any

# 导入数据库服务
from app.services.cosmos_db import CosmosDBService


# ============================================================================
# 用户查询函数
# ============================================================================

async def list_all_users() -> List[Dict[str, Any]]:
    """
    列出数据库中的所有用户。
    
    这是一个跨分区查询，会遍历所有分区获取用户列表。
    在用户量大的情况下可能消耗较多 RU（Request Units）。
    
    Returns:
        List[Dict]: 用户列表，每个元素是一个用户文档
        
    Example:
        >>> users = asyncio.run(list_all_users())
        >>> print(f"Total users: {len(users)}")
    """
    print("Listing all users...")
    print()
    
    # 初始化 Cosmos DB 连接
    db = CosmosDBService()
    await db.initialize()
    
    # 获取 users 容器
    container = db.containers["users"]
    
    # 查询所有用户
    # 使用跨分区查询
    query = "SELECT * FROM c"
    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True,
    ))
    
    # 输出用户列表
    if not items:
        print("No users found in the database.")
        return []
    
    print(f"Found {len(items)} users:")
    print("=" * 60)
    
    for idx, user in enumerate(items, 1):
        print(f"[{idx}] User: {user.get('username', 'N/A')}")
        print(f"    ID: {user.get('id', 'N/A')}")
        print(f"    Email: {user.get('email', 'N/A')}")
        print(f"    Created: {user.get('createdAt', 'N/A')}")
        print(f"    Updated: {user.get('updatedAt', 'N/A')}")
        # 显示用户设置（如果有）
        settings = user.get('settings', {})
        if settings:
            print(f"    Settings: Model={settings.get('defaultModel', 'N/A')}, Theme={settings.get('theme', 'N/A')}")
        print("-" * 60)
    
    print("=" * 60)
    
    return items


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    根据邮箱查询用户。
    
    Args:
        email: 用户邮箱地址
        
    Returns:
        Optional[Dict]: 用户文档，如果不存在则返回 None
    """
    print(f"Searching for user with email: {email}")
    print()
    
    # 初始化 Cosmos DB 连接
    db = CosmosDBService()
    await db.initialize()
    
    # 使用已有的方法查询
    user = await db.get_user_by_email(email)
    
    if not user:
        print(f"User not found with email: {email}")
        return None
    
    # 输出用户信息
    print("User found!")
    print("=" * 60)
    print(f"  ID: {user.get('id', 'N/A')}")
    print(f"  Username: {user.get('username', 'N/A')}")
    print(f"  Email: {user.get('email', 'N/A')}")
    print(f"  Created: {user.get('createdAt', 'N/A')}")
    print(f"  Updated: {user.get('updatedAt', 'N/A')}")
    settings = user.get('settings', {})
    if settings:
        print(f"  Settings: Model={settings.get('defaultModel', 'N/A')}, Theme={settings.get('theme', 'N/A')}")
    print("=" * 60)
    
    return user


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    根据用户 ID 查询用户。
    
    这是一个高效的点读操作，因为 ID 是分区键。
    
    Args:
        user_id: 用户 ID (UUID)
        
    Returns:
        Optional[Dict]: 用户文档，如果不存在则返回 None
    """
    print(f"Searching for user with ID: {user_id}")
    print()
    
    # 初始化 Cosmos DB 连接
    db = CosmosDBService()
    await db.initialize()
    
    # 使用已有的方法查询
    user = await db.get_user_by_id(user_id)
    
    if not user:
        print(f"User not found with ID: {user_id}")
        return None
    
    # 输出用户信息
    print("User found!")
    print("=" * 60)
    print(f"  ID: {user.get('id', 'N/A')}")
    print(f"  Username: {user.get('username', 'N/A')}")
    print(f"  Email: {user.get('email', 'N/A')}")
    print(f"  Created: {user.get('createdAt', 'N/A')}")
    print(f"  Updated: {user.get('updatedAt', 'N/A')}")
    settings = user.get('settings', {})
    if settings:
        print(f"  Settings: Model={settings.get('defaultModel', 'N/A')}, Theme={settings.get('theme', 'N/A')}")
    print("=" * 60)
    
    return user


# ============================================================================
# 脚本入口
# ============================================================================

if __name__ == "__main__":
    # 脚本直接运行时执行
    # 默认列出所有用户
    # 可以取消注释下面的代码来按邮箱或 ID 查询
    
    # 列出所有用户
    asyncio.run(list_all_users())
    
    # 按邮箱查询（取消注释以使用）
    # asyncio.run(get_user_by_email("cl@cl.com"))
    
    # 按 ID 查询（取消注释以使用）
    # asyncio.run(get_user_by_id("your-user-id-here"))