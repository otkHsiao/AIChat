#!/usr/bin/env python3
"""
用户创建脚本。

本脚本用于在 Azure Cosmos DB 中创建新用户，是一个独立的命令行工具。
主要用于初始化系统用户或手动添加用户，不通过 Web API 接口。

使用场景：
1. 系统初始化时创建管理员账户
2. 批量创建测试用户
3. 运维人员手动添加用户

使用方法：
    # 方式1：直接运行脚本（使用脚本中预设的用户信息）
    python create_user.py
    
    # 方式2：修改脚本底部的参数后运行
    asyncio.run(create_user(
        email="newuser@example.com",
        password="secure_password_123",
        username="newuser"  # 可选，不提供时从邮箱提取
    ))

注意事项：
1. 运行前需要设置环境变量（Cosmos DB 连接信息）
2. 密码会使用 bcrypt 算法哈希后存储
3. 邮箱必须唯一，重复邮箱会创建失败
4. 脚本需要在 backend 目录下运行

依赖关系：
┌─────────────────────────────────────────────────────────────────────────┐
│                         用户创建流程                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐                                                    │
│  │  create_user.py  │                                                    │
│  └────────┬─────────┘                                                    │
│           │                                                               │
│           ▼                                                               │
│  ┌────────────────────────────────────────────────────────┐             │
│  │  1. 检查邮箱是否已存在                                    │             │
│  │     └─> CosmosDBService.get_user_by_email()             │             │
│  └────────────────────────────────────────────────────────┘             │
│           │                                                               │
│           ▼                                                               │
│  ┌────────────────────────────────────────────────────────┐             │
│  │  2. 对密码进行 bcrypt 哈希                               │             │
│  │     └─> security.get_password_hash()                    │             │
│  └────────────────────────────────────────────────────────┘             │
│           │                                                               │
│           ▼                                                               │
│  ┌────────────────────────────────────────────────────────┐             │
│  │  3. 创建用户记录                                         │             │
│  │     └─> CosmosDBService.create_user()                   │             │
│  │         - id: UUID                                       │             │
│  │         - email: 邮箱                                    │             │
│  │         - username: 用户名                               │             │
│  │         - passwordHash: 哈希后的密码                      │             │
│  │         - createdAt: 创建时间                            │             │
│  └────────────────────────────────────────────────────────┘             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
"""

import asyncio
import sys
import os

# ============================================================================
# 路径设置
# ============================================================================

# 获取 backend 目录路径（脚本所在目录的父目录）
# __file__ 是当前脚本路径：backend/scripts/create_user.py
# 第一个 dirname 得到：backend/scripts
# 第二个 dirname 得到：backend
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 将 backend 目录添加到 Python 路径
# 这样就能正确导入 app.services.cosmos_db 等模块
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

from typing import Optional

# 导入数据库服务和密码哈希函数
from app.services.cosmos_db import CosmosDBService
from app.core.security import get_password_hash


# ============================================================================
# 用户创建函数
# ============================================================================

async def create_user(email: str, password: str, username: Optional[str] = None):
    """
    在 Cosmos DB 中创建新用户。
    
    这是一个异步函数，执行以下步骤：
    1. 如果未提供用户名，从邮箱中提取（@ 之前的部分）
    2. 初始化 Cosmos DB 连接
    3. 检查邮箱是否已被注册
    4. 对密码进行 bcrypt 哈希
    5. 创建用户记录并存入数据库
    
    安全特性：
    - 密码使用 bcrypt 算法哈希，不存储明文
    - 邮箱唯一性验证，防止重复注册
    
    Args:
        email: 用户邮箱（必须唯一）
        password: 明文密码（会被哈希后存储）
        username: 用户名（可选，默认从邮箱提取）
        
    Returns:
        dict: 创建成功时返回用户信息字典
        None: 创建失败时返回 None（如邮箱已存在）
        
    Example:
        >>> asyncio.run(create_user("admin@example.com", "admin123"))
        Creating user: admin@example.com
        Username: admin
        User created successfully!
          ID: 550e8400-e29b-41d4-a716-446655440000
          Email: admin@example.com
          Username: admin
          Created: 2024-01-01T00:00:00.000Z
    """
    # 如果没有提供用户名，从邮箱地址提取
    # 例如："john@example.com" -> "john"
    if username is None:
        username = email.split("@")[0]
    
    print(f"Creating user: {email}")
    print(f"Username: {username}")
    
    # 初始化 Cosmos DB 连接
    # 需要环境变量：
    # - AZURE_COSMOSDB_ENDPOINT
    # - AZURE_COSMOSDB_KEY
    # - AZURE_COSMOSDB_DATABASE
    db = CosmosDBService()
    await db.initialize()
    
    # 检查邮箱是否已被注册
    # 返回 None 表示未注册
    existing_user = await db.get_user_by_email(email)
    if existing_user:
        print(f"Error: User with email {email} already exists!")
        return None
    
    # 使用 bcrypt 算法对密码进行哈希
    # bcrypt 自动处理盐值生成和哈希
    password_hash = get_password_hash(password)
    
    # 创建用户记录
    # create_user 方法会自动添加 id 和 createdAt 字段
    user = await db.create_user({
        "email": email,
        "username": username,
        "passwordHash": password_hash,
    })
    
    # 打印创建成功信息
    print(f"User created successfully!")
    print(f"  ID: {user['id']}")
    print(f"  Email: {user['email']}")
    print(f"  Username: {user['username']}")
    print(f"  Created: {user['createdAt']}")
    
    return user


# ============================================================================
# 脚本入口
# ============================================================================

if __name__ == "__main__":
    # 脚本直接运行时执行
    # 可以修改这里的参数来创建不同的用户
    
    # 示例：创建一个测试用户
    # 建议通过环境变量传递密码，不要硬编码
    # password = os.getenv("USER_PASSWORD", "default_secure_password")
    asyncio.run(create_user(
        email="user@example.com",
        password="change_me_123",
        username="user"
    ))