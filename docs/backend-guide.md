# 后端架构与代码指南（前端开发者入门）

## 🎯 概述

本项目后端使用 **FastAPI** 框架构建，是一个基于 Python 的高性能异步 Web 框架。作为前端开发者，这份指南将帮助你快速理解后端代码结构和核心概念。

---

## 📁 目录结构

```
backend/app/
├── main.py                    # 🚀 应用入口点
├── api/                       # 📡 API 路由层
│   ├── __init__.py           # 路由注册中心
│   ├── auth.py               # 认证相关 API
│   ├── chat.py               # 聊天/消息 API
│   ├── conversations.py      # 对话管理 API
│   └── files.py              # 文件上传 API
├── core/                      # ⚙️ 核心模块
│   ├── config.py             # 配置管理
│   ├── dependencies.py       # 依赖注入
│   ├── security.py           # 安全工具（JWT、密码）
│   └── sanitizer.py          # 输入清理
├── schemas/                   # 📋 数据模型（类似 TypeScript 的 interface）
│   ├── auth.py               # 认证相关模型
│   ├── conversation.py       # 对话模型
│   ├── message.py            # 消息模型
│   └── file.py               # 文件模型
└── services/                  # 🔧 业务服务层
    ├── azure_openai.py       # Azure OpenAI 服务
    ├── cosmos_db.py          # 数据库服务
    └── blob_storage.py       # 文件存储服务
```

---

## 🔑 核心概念对照（前端 vs 后端）

| 前端概念 | 后端对应 | 说明 |
|---------|---------|------|
| TypeScript interface | Pydantic Schema | 数据类型定义和验证 |
| API hooks (RTK Query) | API Router | 定义 API 端点 |
| Redux Slice | Service 类 | 业务逻辑封装 |
| Context Provider | 依赖注入 | 共享状态/服务 |
| Middleware | Middleware | 请求/响应拦截 |
| Environment Variables | `.env` + `config.py` | 配置管理 |

---

## 📖 核心模块详解

### 1️⃣ 入口文件 [`main.py`](../backend/app/main.py)

这是应用的启动点，类似于前端的 `main.tsx`。

```python
# 关键组成部分
from fastapi import FastAPI

# 1. 创建应用实例（类似 createRoot()）
app = FastAPI(
    title="AI Chat API",
    docs_url="/docs",  # Swagger 文档
)

# 2. 配置中间件（类似 Redux middleware）
app.add_middleware(CORSMiddleware, ...)

# 3. 注册路由（类似 React Router 的 <Routes>）
app.include_router(api_router, prefix="/api")

# 4. 生命周期管理（类似 useEffect 的 cleanup）
@asynccontextmanager
async def lifespan(app):
    # 启动时执行
    yield
    # 关闭时执行
```

**快速理解**：
- `lifespan` 函数管理应用启动/关闭
- `CORSMiddleware` 处理跨域，就像前端 proxy 配置
- 所有 API 都在 `/api` 前缀下

---

### 2️⃣ API 路由 [`api/`](../backend/app/api/__init__.py)

路由定义了 HTTP 端点，类似于前端的 API service。

#### 路由注册 [`api/__init__.py`](../backend/app/api/__init__.py)

```python
from fastapi import APIRouter

api_router = APIRouter()

# 注册子路由（类似 React Router 嵌套路由）
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["会话"])
api_router.include_router(chat.router, tags=["聊天"])
api_router.include_router(files.router, prefix="/files", tags=["文件"])
```

#### API 端点示例 [`api/auth.py`](../backend/app/api/auth.py:148)

```python
@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")  # 速率限制
async def login(
    request: Request,
    credentials: UserLogin,      # 自动验证请求体
    db: CosmosDB,                # 依赖注入数据库
) -> TokenResponse:
    # 业务逻辑
    user = await db.get_user_by_email(credentials.email)
    if not verify_password(credentials.password, user["passwordHash"]):
        raise HTTPException(status_code=401, detail="密码错误")
    
    # 生成 JWT
    access_token = create_access_token(subject=user["id"])
    return TokenResponse(user=user, accessToken=access_token, ...)
```

**前端开发者注意**：
- `@router.post("/login")` → 定义 `POST /api/auth/login`
- `response_model=TokenResponse` → 响应类型（自动生成 Swagger 文档）
- `credentials: UserLogin` → 自动验证请求体，类似前端的 Zod
- `db: CosmosDB` → 依赖注入，自动获取数据库实例

---

### 3️⃣ 依赖注入 [`core/dependencies.py`](../backend/app/core/dependencies.py)

依赖注入类似于 React 的 Context，让组件/函数可以访问共享资源。

```python
from typing import Annotated
from fastapi import Depends

# 定义依赖函数
async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials,
) -> str:
    token = credentials.credentials
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401)
    return user_id

# 创建类型别名（类似 TypeScript 的 type alias）
CurrentUserId = Annotated[str, Depends(get_current_user_id)]

# 使用时只需在参数中声明
@router.get("/me")
async def get_me(user_id: CurrentUserId):  # 自动注入已验证的用户 ID
    return {"user_id": user_id}
```

**主要依赖项**：
- `CurrentUserId` - 需要认证的用户 ID
- `OptionalUserId` - 可选认证
- `CosmosDB` - 数据库服务实例

---

### 4️⃣ Schemas（数据模型）[`schemas/`](../backend/app/schemas/auth.py)

Pydantic Schema 类似于 TypeScript 的 interface，但更强大：

```python
from pydantic import BaseModel, EmailStr, Field

class UserLogin(BaseModel):
    """登录请求模型"""
    email: EmailStr                    # 自动验证邮箱格式
    password: str

class UserCreate(BaseModel):
    """注册请求模型"""
    email: EmailStr
    username: str = Field(
        min_length=3, 
        max_length=50, 
        pattern=r"^[a-zA-Z0-9_]+$"    # 正则验证
    )
    password: str = Field(min_length=8)

class UserResponse(BaseModel):
    """响应模型"""
    id: str
    email: str
    username: str
    createdAt: str
    settings: Optional[UserSettings] = None
```

**对比 TypeScript**：
```typescript
// TypeScript
interface UserLogin {
    email: string;
    password: string;
}

// Python Pydantic（更强大，自带验证）
class UserLogin(BaseModel):
    email: EmailStr      # 自动验证格式
    password: str
```

---

### 5️⃣ 服务层 [`services/`](../backend/app/services/cosmos_db.py)

服务层封装业务逻辑，类似于前端的 API service 或 Redux thunk。

#### 数据库服务 [`cosmos_db.py`](../backend/app/services/cosmos_db.py:71)

```python
class CosmosDBService:
    """封装所有数据库操作"""
    
    async def create_user(self, user_data: dict) -> dict:
        """创建用户"""
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": user_data["email"],
            ...
        }
        self.containers["users"].create_item(body=user)
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """根据邮箱查找用户"""
        query = "SELECT * FROM c WHERE c.email = @email"
        items = list(self.container.query_items(query, ...))
        return items[0] if items else None
```

#### Azure OpenAI 服务 [`azure_openai.py`](../backend/app/services/azure_openai.py:51)

```python
class AzureOpenAIService:
    """AI 聊天服务"""
    
    async def chat_completion_stream(self, ...):
        """流式聊天响应（SSE）"""
        stream = await self.async_client.chat.completions.create(
            model=self.deployment_name,
            messages=messages,
            stream=True,  # 启用流式
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield {
                    "type": "content_delta",
                    "delta": chunk.choices[0].delta.content,
                }
```

---

### 6️⃣ 安全模块 [`core/security.py`](../backend/app/core/security.py)

处理密码哈希和 JWT 令牌：

```python
# 密码哈希（使用 bcrypt）
def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

# JWT 令牌
def create_access_token(subject: str) -> str:
    payload = {
        "sub": subject,           # 用户 ID
        "exp": datetime.utcnow() + timedelta(hours=24),
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")  # 返回用户 ID
    except JWTError:
        return None
```

---

## 🔄 请求处理流程

```
客户端请求 → CORS 中间件 → 速率限制 → 认证 → 路由处理 → 响应
     ↓
     ↓ POST /api/auth/login
     ↓
┌────────────────────────────────────────────────────────────────┐
│ 1. CORSMiddleware: 检查跨域                                     │
│ 2. Limiter: 检查速率限制 (10/minute)                            │
│ 3. Router: 匹配路由 /api/auth/login                             │
│ 4. Pydantic: 验证请求体 UserLogin                               │
│ 5. Dependencies: 注入 CosmosDB                                  │
│ 6. Handler: 执行 login() 函数                                   │
│ 7. Response: 返回 TokenResponse                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 📡 API 端点清单

### 认证 `/api/auth`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/login` | 用户登录 | ❌ |
| POST | `/register` | 用户注册（已禁用） | ❌ |
| POST | `/refresh` | 刷新令牌 | ❌ |
| GET | `/me` | 获取当前用户 | ✅ |
| PUT | `/settings` | 更新用户设置 | ✅ |
| PUT | `/password` | 修改密码 | ✅ |

### 对话 `/api/conversations`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/` | 获取对话列表 | ✅ |
| POST | `/` | 创建对话 | ✅ |
| GET | `/{id}` | 获取对话详情 | ✅ |
| PUT | `/{id}` | 更新对话 | ✅ |
| DELETE | `/{id}` | 删除对话 | ✅ |

### 聊天 `/api/conversations/{id}/messages`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/` | 获取消息历史 | ✅ |
| POST | `/` | 发送消息（非流式） | ✅ |
| POST | `/stream` | 发送消息（流式 SSE） | ✅ |

### 文件 `/api/files`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/upload` | 上传文件 | ✅ |

---

## 🚀 本地开发

### 环境设置

```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境
python -m venv .venv

# 3. 激活虚拟环境（Windows）
.venv\Scripts\activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 复制环境变量
cp .env.example .env
# 编辑 .env 填入实际值
```

### 启动服务

```bash
# 开发模式（热重载）
uvicorn app.main:app --reload --port 8000

# 或直接运行
python -m app.main
```

### 访问文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🔧 常用开发任务

### 添加新 API 端点

1. 在 `schemas/` 创建请求/响应模型
2. 在 `api/` 对应文件添加路由
3. 在 `services/` 添加业务逻辑（如需要）

```python
# 1. 定义 Schema
class MyRequest(BaseModel):
    name: str

# 2. 添加路由
@router.post("/my-endpoint")
async def my_handler(
    data: MyRequest,
    user_id: CurrentUserId,
    db: CosmosDB,
):
    # 业务逻辑
    return {"success": True}
```

### 添加新数据库操作

在 [`cosmos_db.py`](../backend/app/services/cosmos_db.py:71) 添加方法：

```python
async def my_new_operation(self, param: str) -> dict:
    container = self._get_container("my_collection")
    # ... 数据库操作
    return result
```

---

## 📝 快速对照表

| 你想做的事 | 前端做法 | 后端做法 |
|-----------|---------|---------|
| 定义数据类型 | TypeScript interface | Pydantic BaseModel |
| 调用 API | fetch / axios | FastAPI router |
| 状态管理 | Redux | 依赖注入 + 单例服务 |
| 环境变量 | `.env` + import.meta.env | `.env` + Pydantic Settings |
| 表单验证 | Zod / Yup | Pydantic Field |
| 请求拦截 | Axios interceptor | FastAPI Middleware |
| 错误处理 | try/catch | HTTPException |

---

## ❓ 常见问题

### Q: 为什么使用 `async/await`？

Python 的 FastAPI 和 Node.js 类似，使用异步 I/O 提高并发性能。每个请求处理函数都是 `async def`。

### Q: `Depends()` 是什么？

类似 React 的 `useContext`，FastAPI 会自动注入依赖项。

### Q: 如何调试？

1. 使用 `/docs` 的 Swagger UI 测试 API
2. 在代码中使用 `print()` 或 `logging`
3. 使用 VS Code 的 Python 调试器

---

*文档版本：1.0 | 创建时间：2024-12-22*