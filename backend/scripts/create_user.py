#!/usr/bin/env python3
"""Script to create a new user in Cosmos DB."""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional

from app.services.cosmos_db import CosmosDBService
from app.core.security import get_password_hash


async def create_user(email: str, password: str, username: Optional[str] = None):
    """Create a new user in the database."""
    if username is None:
        username = email.split("@")[0]
    
    print(f"Creating user: {email}")
    print(f"Username: {username}")
    
    # Initialize Cosmos DB
    db = CosmosDBService()
    await db.initialize()
    
    # Check if user already exists
    existing_user = await db.get_user_by_email(email)
    if existing_user:
        print(f"Error: User with email {email} already exists!")
        return None
    
    # Hash password
    password_hash = get_password_hash(password)
    
    # Create user
    user = await db.create_user({
        "email": email,
        "username": username,
        "passwordHash": password_hash,
    })
    
    print(f"User created successfully!")
    print(f"  ID: {user['id']}")
    print(f"  Email: {user['email']}")
    print(f"  Username: {user['username']}")
    print(f"  Created: {user['createdAt']}")
    
    return user


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