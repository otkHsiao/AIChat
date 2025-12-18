# AI Chat 项目指南

## 项目概述

这是一个类似 ChatGPT 的智能聊天应用，支持多轮对话、流式响应、文件上传和图片分析功能。

### 访问地址

- **前端应用**: https://app-ai-chat-frontend-xc.azurewebsites.net/
- **后端 API**: https://app-ai-chat-backend-xc.azurewebsites.net/
- **API 文档**: https://app-ai-chat-backend-xc.azurewebsites.net/docs (开发模式)

---

## Azure 服务架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Azure Cloud (East Asia)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐     ┌──────────────────┐     ┌─────────────────┐  │
│  │   Azure Key      │     │  Azure Container │     │  Azure OpenAI   │  │
│  │   Vault          │     │  Registry (ACR)  │     │  Service        │  │
│  │                  │     │                  │     │                 │  │
│  │  kv-ai-chat-xc   │     │  acraichatxc     │     │  GPT-4o Model   │  │
│  └────────┬─────────┘     └────────┬─────────┘     └────────┬────────┘  │
│           │                        │                        │           │
│           │ Key Vault References   │ Docker Images          │ API       │
│           ▼                        ▼                        ▼           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Azure App Service Plan                        │   │
│  │                    (plan-ai-chat-xc - Linux B1)                  │   │
│  │  ┌─────────────────────────┐  ┌─────────────────────────┐       │   │
│  │  │  Frontend Web App       │  │  Backend Web App        │       │   │
│  │  │  app-ai-chat-frontend-xc│  │  app-ai-chat-backend-xc │       │   │
│  │  │                         │  │                         │       │   │
│  │  │  - React SPA            │  │  - FastAPI              │       │   │
│  │  │  - Nginx Reverse Proxy  │──│  - Python 3.11          │       │   │
│  │  │  - Fluent UI v9         │  │  - JWT Auth             │       │   │
│  │  └─────────────────────────┘  └───────────┬─────────────┘       │   │
│  └───────────────────────────────────────────┼─────────────────────┘   │
│                                              │                          │
│           ┌──────────────────────────────────┼──────────────────────┐  │
│           │                                  │                      │  │
│           ▼                                  ▼                      ▼  │
│  ┌─────────────────┐              ┌─────────────────┐    ┌──────────┐ │
│  │  Azure Cosmos   │              │  Azure Blob     │    │ Managed  │ │
│  │  DB (NoSQL)     │              │  Storage        │    │ Identity │ │
│  │                 │              │                 │    │          │ │
│  │  cosmos-ai-chat │              │  staichat...    │    │ Backend  │ │
│  │  -xc            │              │                 │    │ Frontend │ │
│  │                 │              │                 │    │          │ │
│  │  - users        │              │  - file-uploads │    └──────────┘ │
│  │  - conversations│              │                 │                  │
│  │  - messages     │              └─────────────────┘                  │
│  └─────────────────┘                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Azure 服务详细说明

### 1. Resource Group (资源组)
| 属性 | 值 |
|------|-----|
| **名称** | `rg-ai-chat` |
| **区域** | East Asia |
| **用途** | 组织和管理所有相关 Azure 资源 |

### 2. Azure Container Registry (容器注册表)
| 属性 | 值 |
|------|-----|
| **名称** | `acraichatxc` |
| **SKU** | Basic |
| **登录服务器** | `acraichatxc.azurecr.io` |
| **用途** | 存储和管理 Docker 镜像 |

**存储的镜像**:
- `ai-chat-frontend:latest` - 前端 React 应用镜像
- `ai-chat-backend:latest` - 后端 FastAPI 应用镜像

### 3. Azure App Service Plan (应用服务计划)
| 属性 | 值 |
|------|-----|
| **名称** | `plan-ai-chat-xc` |
| **SKU** | B1 (Basic) |
| **操作系统** | Linux |
| **用途** | 托管 Web 应用的计算资源 |

### 4. Azure App Service - Frontend (前端 Web 应用)
| 属性 | 值 |
|------|-----|
| **名称** | `app-ai-chat-frontend-xc` |
| **URL** | https://app-ai-chat-frontend-xc.azurewebsites.net |
| **容器镜像** | `acraichatxc.azurecr.io/ai-chat-frontend:latest` |
| **托管身份 ID** | `c1e65130-510d-442f-bc2a-e917977a2f77` |

**功能说明**:
- 托管 React 单页应用 (SPA)
- 使用 Nginx 作为反向代理，将 `/api/*` 请求转发到后端
- 提供静态资源服务和 Gzip 压缩

**环境变量**:
| 变量名 | 值 |
|--------|-----|
| `API_URL` | https://app-ai-chat-backend-xc.azurewebsites.net |

### 5. Azure App Service - Backend (后端 Web 应用)
| 属性 | 值 |
|------|-----|
| **名称** | `app-ai-chat-backend-xc` |
| **URL** | https://app-ai-chat-backend-xc.azurewebsites.net |
| **容器镜像** | `acraichatxc.azurecr.io/ai-chat-backend:latest` |
| **托管身份 ID** | `0b32d19d-c99b-4236-afeb-3b4ecf3cd72f` |

**功能说明**:
- 托管 FastAPI 应用程序
- 提供 RESTful API 和 SSE 流式响应
- 处理用户认证、对话管理、文件上传

**环境变量** (通过 Key Vault 引用):
| 变量名 | 说明 |
|--------|------|
| `AZURE_OPENAI_API_KEY` | OpenAI API 密钥 |
| `AZURE_OPENAI_ENDPOINT` | OpenAI 服务端点 |
| `COSMOS_CONNECTION_STRING` | Cosmos DB 连接字符串 |
| `BLOB_CONNECTION_STRING` | Blob Storage 连接字符串 |
| `JWT_SECRET_KEY` | JWT 签名密钥 |

### 6. Azure Key Vault (密钥保管库)
| 属性 | 值 |
|------|-----|
| **名称** | `kv-ai-chat-xc` |
| **SKU** | Standard |
| **用途** | 安全存储敏感配置和密钥 |

**存储的密钥**:
| 密钥名称 | 说明 |
|----------|------|
| `azure-openai-api-key` | Azure OpenAI API 密钥 |
| `azure-openai-endpoint` | Azure OpenAI 服务端点 |
| `cosmos-connection-string` | Cosmos DB 连接字符串 |
| `blob-connection-string` | Blob Storage 连接字符串 |
| `jwt-secret-key` | JWT 令牌签名密钥 |
| `acr-password` | ACR 访问密码 |

### 7. Azure Cosmos DB (NoSQL 数据库)
| 属性 | 值 |
|------|-----|
| **账户名** | `cosmos-ai-chat-xc` |
| **API** | NoSQL (SQL API) |
| **数据库名** | `ai-chat` |

**容器 (Collections)**:
| 容器名 | 分区键 | 用途 |
|--------|--------|------|
| `users` | `/id` | 存储用户账户信息 |
| `conversations` | `/userId` | 存储对话会话 |
| `messages` | `/conversationId` | 存储对话消息 |

### 8. Azure Blob Storage (对象存储)
| 属性 | 值 |
|------|-----|
| **存储账户** | `staichat...` |
| **容器名** | `file-uploads` |
| **访问级别** | Private |

**用途**:
- 存储用户上传的文件
- 支持图片、文档等多种格式
- 支持最大 10MB 文件大小

### 9. Azure OpenAI Service (AI 服务)
| 属性 | 值 |
|------|-----|
| **模型** | GPT-4o |
| **API 版本** | 2024-02-15-preview |
| **用途** | 提供智能对话能力 |

**功能**:
- 多轮对话上下文理解
- 流式响应 (SSE)
- 图片分析 (Vision)
- 文件内容理解

### 10. Managed Identity (托管身份)

**后端托管身份**: `0b32d19d-c99b-4236-afeb-3b4ecf3cd72f`
- 访问 Key Vault 读取密钥
- 访问 Cosmos DB
- 访问 Blob Storage

**前端托管身份**: `c1e65130-510d-442f-bc2a-e917977a2f77`
- 访问 Key Vault (如需要)

---

## 项目目录结构

```
ai-chat/
├── backend/                    # 后端 FastAPI 应用
│   ├── app/                   # 应用主目录
│   │   ├── __init__.py       # 包初始化
│   │   ├── main.py           # FastAPI 应用入口，路由配置，中间件
│   │   ├── api/              # API 路由模块
│   │   │   ├── __init__.py   # 路由聚合，导出 api_router
│   │   │   ├── auth.py       # 认证 API：登录、注册(已禁用)、刷新令牌
│   │   │   ├── conversations.py  # 对话 API：创建、列表、删除对话 (速率限制)
│   │   │   ├── messages.py   # 消息 API：发送消息、流式响应
│   │   │   ├── chat.py       # 聊天 API：消息发送、历史记录 (速率限制)
│   │   │   └── files.py      # 文件 API：上传、下载、删除文件 (速率限制)
│   │   ├── core/             # 核心模块
│   │   │   ├── __init__.py
│   │   │   ├── config.py     # 配置管理，环境变量读取
│   │   │   ├── security.py   # 安全模块：密码哈希、JWT 生成验证
│   │   │   ├── sanitizer.py  # 输入清理：XSS 防护、HTML 过滤
│   │   │   └── dependencies.py   # 依赖注入：数据库连接、当前用户
│   │   ├── models/           # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py       # 用户模型
│   │   │   ├── conversation.py   # 对话模型
│   │   │   └── message.py    # 消息模型
│   │   ├── schemas/          # Pydantic 模式（请求/响应）
│   │   │   ├── __init__.py
│   │   │   ├── common.py     # 通用响应模式
│   │   │   ├── auth.py       # 认证相关模式
│   │   │   ├── conversation.py   # 对话相关模式
│   │   │   └── file.py       # 文件相关模式
│   │   └── services/         # 业务服务
│   │       ├── __init__.py
│   │       ├── cosmos_db.py  # Cosmos DB 服务封装
│   │       ├── blob_storage.py   # Blob Storage 服务封装
│   │       └── openai_service.py # OpenAI API 服务封装
│   ├── Dockerfile            # 后端 Docker 构建文件
│   ├── pyproject.toml        # Python 项目配置，依赖定义
│   ├── requirements.txt      # Python 依赖列表
│   └── .env.example          # 环境变量示例
│
├── frontend/                  # 前端 React 应用
│   ├── src/                  # 源代码目录
│   │   ├── main.tsx          # 应用入口，渲染根组件
│   │   ├── App.tsx           # 根组件，路由配置
│   │   ├── components/       # React 组件
│   │   │   ├── Layout/       # 布局组件
│   │   │   │   ├── MainLayout.tsx    # 主布局
│   │   │   │   └── Sidebar.tsx       # 侧边栏
│   │   │   ├── Chat/         # 聊天组件
│   │   │   │   ├── ChatContainer.tsx # 聊天容器
│   │   │   │   ├── MessageList.tsx   # 消息列表
│   │   │   │   ├── MessageItem.tsx   # 单条消息
│   │   │   │   └── ChatInput.tsx     # 输入框
│   │   │   ├── Auth/         # 认证组件
│   │   │   │   ├── LoginForm.tsx     # 登录表单
│   │   │   │   └── RegisterForm.tsx  # 注册表单
│   │   │   ├── ErrorBoundary/  # 错误边界组件
│   │   │   │   └── ErrorBoundary.tsx # 全局错误捕获
│   │   │   ├── Toast/         # Toast 通知组件
│   │   │   │   ├── ToastProvider.tsx # Toast 上下文提供者
│   │   │   │   └── index.ts          # 导出
│   │   │   ├── Skeleton/      # 骨架屏组件
│   │   │   │   ├── ChatSkeleton.tsx  # 聊天加载骨架
│   │   │   │   ├── SidebarSkeleton.tsx # 侧边栏骨架
│   │   │   │   └── index.ts          # 导出
│   │   │   ├── LazyImage/     # 图片懒加载组件
│   │   │   │   ├── LazyImage.tsx     # 懒加载图片
│   │   │   │   └── index.ts          # 导出
│   │   │   ├── OfflineIndicator/  # 离线状态指示器
│   │   │   │   └── OfflineIndicator.tsx
│   │   │   └── common/       # 通用组件
│   │   │       └── Loading.tsx       # 加载状态
│   │   ├── pages/            # 页面组件
│   │   │   ├── HomePage.tsx  # 首页/聊天页
│   │   │   ├── LoginPage.tsx # 登录页
│   │   │   └── RegisterPage.tsx  # 注册页
│   │   ├── store/            # Redux 状态管理
│   │   │   ├── index.ts      # Store 配置
│   │   │   ├── slices/       # Redux Slices
│   │   │   │   ├── authSlice.ts      # 认证状态
│   │   │   │   ├── chatSlice.ts      # 聊天状态
│   │   │   │   └── uiSlice.ts        # UI 状态
│   │   │   └── api/          # RTK Query API
│   │   │       ├── authApi.ts        # 认证 API
│   │   │       ├── conversationApi.ts # 对话 API
│   │   │       └── messageApi.ts     # 消息 API
│   │   ├── hooks/            # 自定义 Hooks
│   │   │   ├── useAuth.ts    # 认证 Hook
│   │   │   ├── useChat.ts    # 聊天 Hook
│   │   │   ├── useMediaQuery.ts  # 响应式媒体查询
│   │   │   └── useOnlineStatus.ts # 在线状态检测
│   │   ├── utils/            # 工具函数
│   │   │   ├── api.ts        # API 客户端
│   │   │   └── storage.ts    # 本地存储
│   │   └── types/            # TypeScript 类型定义
│   │       └── index.ts      # 类型导出
│   ├── public/               # 静态资源
│   │   └── favicon.ico       # 网站图标
│   ├── Dockerfile            # 前端 Docker 构建文件
│   ├── nginx.conf.template   # Nginx 配置模板
│   ├── docker-entrypoint.sh  # Docker 入口脚本
│   ├── package.json          # NPM 包配置
│   ├── vite.config.ts        # Vite 构建配置
│   ├── tsconfig.json         # TypeScript 配置
│   └── index.html            # HTML 入口
│
├── deploy/                    # 部署配置
│   ├── README.md             # 部署说明
│   ├── kv-appsettings.json   # 后端 Key Vault 配置
│   └── kv-frontend-appsettings.json  # 前端配置
│
├── docs/                      # 项目文档
│   ├── PROJECT-GUIDE.md      # 项目指南（本文档）
│   ├── api-spec.md           # API 规范
│   ├── architecture.md       # 架构设计
│   ├── azure-setup.md        # Azure 部署指南
│   ├── env-config.md         # 环境配置说明
│   └── todo.md               # 待办事项
│
├── .gitignore                # Git 忽略文件
└── README.md                 # 项目说明
```

---

## 核心文件说明

### 后端文件

| 文件路径 | 说明 |
|----------|------|
| `backend/app/main.py` | FastAPI 应用入口，配置中间件、路由、异常处理 |
| `backend/app/core/config.py` | 使用 Pydantic Settings 管理配置，支持环境变量 |
| `backend/app/core/security.py` | JWT 令牌生成/验证，密码哈希 (bcrypt) |
| `backend/app/core/dependencies.py` | 依赖注入：数据库实例、当前用户获取 |
| `backend/app/api/auth.py` | 认证 API：POST /register, POST /login, POST /refresh |
| `backend/app/api/conversations.py` | 对话管理：GET/POST/DELETE /conversations |
| `backend/app/api/messages.py` | 消息 API：POST /messages, GET /messages/stream |
| `backend/app/services/cosmos_db.py` | Cosmos DB CRUD 操作封装 |
| `backend/app/services/openai_service.py` | OpenAI API 调用，支持流式响应 |
| `backend/Dockerfile` | 多阶段构建，使用 Python 3.11 slim 镜像 |

### 前端文件

| 文件路径 | 说明 |
|----------|------|
| `frontend/src/main.tsx` | React 应用入口，Provider 配置 |
| `frontend/src/App.tsx` | 路由配置，使用 React Router |
| `frontend/src/store/index.ts` | Redux Store 配置，集成 RTK Query |
| `frontend/src/store/slices/authSlice.ts` | 认证状态管理：用户信息、令牌 |
| `frontend/src/store/slices/chatSlice.ts` | 聊天状态：对话列表、当前对话、消息 |
| `frontend/src/store/api/` | RTK Query API 定义，自动生成 hooks |
| `frontend/src/components/Chat/` | 聊天 UI 组件：消息列表、输入框 |
| `frontend/nginx.conf.template` | Nginx 配置：静态资源、API 反向代理、SSE 支持 |
| `frontend/docker-entrypoint.sh` | 启动脚本，使用 envsubst 替换环境变量 |
| `frontend/Dockerfile` | 多阶段构建：Node 构建 + Nginx 运行 |

### 部署文件

| 文件路径 | 说明 |
|----------|------|
| `deploy/kv-appsettings.json` | 后端 App Service 环境变量配置 (Key Vault 引用) |
| `deploy/kv-frontend-appsettings.json` | 前端 App Service 环境变量配置 |

---

## 快速开始

### 本地开发

#### 后端
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
cp .env.example .env
# 编辑 .env 配置环境变量
uvicorn app.main:app --reload
```

#### 前端
```bash
cd frontend
npm install
npm run dev
```

### Docker 部署

```bash
# 构建镜像
docker build -t ai-chat-backend:latest -f backend/Dockerfile backend
docker build -t ai-chat-frontend:latest -f frontend/Dockerfile frontend

# 运行容器
docker run -d -p 8000:8000 --env-file backend/.env ai-chat-backend:latest
docker run -d -p 80:80 -e API_URL=http://localhost:8000 ai-chat-frontend:latest
```

### Azure 部署

详见 [Azure 部署指南](./azure-setup.md)

---

## API 端点摘要

### 认证 API
| 方法 | 端点 | 说明 | 速率限制 |
|------|------|------|---------|
| POST | `/api/auth/register` | 用户注册 (已禁用) | - |
| POST | `/api/auth/login` | 用户登录 | - |
| POST | `/api/auth/refresh` | 刷新令牌 | - |
| GET | `/api/auth/me` | 获取当前用户 | - |

### 对话 API
| 方法 | 端点 | 说明 | 速率限制 |
|------|------|------|---------|
| GET | `/api/conversations` | 获取对话列表 | 60/分钟 |
| POST | `/api/conversations` | 创建新对话 | 30/分钟 |
| GET | `/api/conversations/{id}` | 获取对话详情 | 60/分钟 |
| DELETE | `/api/conversations/{id}` | 删除对话 | 30/分钟 |

### 消息 API
| 方法 | 端点 | 说明 | 速率限制 |
|------|------|------|---------|
| POST | `/api/conversations/{id}/messages` | 发送消息 | 20/分钟 |
| GET | `/api/conversations/{id}/messages` | 获取消息历史 | 60/分钟 |
| POST | `/api/conversations/{id}/messages/stream` | 流式发送消息 (SSE) | 20/分钟 |

### 文件 API
| 方法 | 端点 | 说明 | 速率限制 |
|------|------|------|---------|
| POST | `/api/files/upload` | 上传文件 | 30/分钟 |
| GET | `/api/files/{id}` | 下载文件 | - |
| DELETE | `/api/files/{id}` | 删除文件 | - |

---

## 安全配置

### 认证流程
1. 用户注册/登录获取 JWT 令牌
2. 访问令牌 (Access Token) 有效期 24 小时
3. 刷新令牌 (Refresh Token) 有效期 7 天
4. 令牌存储在 localStorage，API 请求通过 Authorization 头传递

### Key Vault 引用格式
```
@Microsoft.KeyVault(SecretUri=https://kv-ai-chat-xc.vault.azure.net/secrets/{secret-name}/)
```

### CORS 配置
- 允许来源：前端域名
- 允许方法：GET, POST, PUT, DELETE, OPTIONS
- 允许凭证：是

### 速率限制
后端使用 `slowapi` 库实现 API 速率限制，防止滥用：
- 消息发送：20 次/分钟
- 对话列表：60 次/分钟
- 对话创建：30 次/分钟
- 文件上传：30 次/分钟

### 输入清理
后端实现了输入清理机制，防止 XSS 和注入攻击：
- HTML 标签过滤
- 特殊字符转义
- 输入长度限制

---

## 监控与日志

### 健康检查端点
- 后端：`GET /health` → `{"status":"healthy","environment":"development"}`
- 前端：`GET /health` → `healthy`

### 日志查看
```bash
# 查看后端日志
az webapp log tail --name app-ai-chat-backend-xc --resource-group rg-ai-chat

# 查看前端日志
az webapp log tail --name app-ai-chat-frontend-xc --resource-group rg-ai-chat
```

---

## 成本估算 (月度)

| 服务 | SKU | 预估成本 |
|------|-----|---------|
| App Service Plan | B1 | ~$13 |
| Cosmos DB | Serverless | ~$5-20 (按使用量) |
| Blob Storage | Hot | ~$1-5 |
| Key Vault | Standard | ~$0.03/操作 |
| Container Registry | Basic | ~$5 |
| Azure OpenAI | GPT-4o | 按 token 计费 |

**总计**: 约 $25-50/月 (不含 OpenAI API 费用)

---

## 常见问题

### Q: 登录返回 405 错误
**A**: 检查 nginx 配置的 `proxy_pass` 和 Host 头设置

### Q: 无法连接 Cosmos DB
**A**: 检查 Key Vault 中的连接字符串是否正确

### Q: 图片分析不工作
**A**: 确认使用支持 Vision 的模型 (如 GPT-4o)

### Q: 流式响应卡顿
**A**: 检查 nginx 是否禁用了 `proxy_buffering`

---

## 更新日志

### v0.2.0 (2025-12-18)
- **移动端优化**: 响应式 Sidebar，触摸友好的 UI
- **错误处理**: 全局 ErrorBoundary，Toast 通知系统
- **加载体验**: 聊天和侧边栏骨架屏组件
- **性能优化**: 图片懒加载 (IntersectionObserver)
- **离线支持**: 离线状态指示器
- **安全加固**:
  - API 速率限制 (slowapi)
  - 输入清理和验证
  - 注册 API 已禁用

### v0.1.0 (2025-12-18)
- 初始版本发布
- 实现用户认证
- 实现多轮对话
- 支持流式响应
- 支持文件上传和图片分析
- Azure 部署完成
- Key Vault 集成完成