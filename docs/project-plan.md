# AI Chat 项目执行计划

## 项目概述

构建一个类似ChatGPT的智能聊天应用，支持多用户、多会话、文件上传和自定义Prompt。

## 技术栈确认

| 层级 | 技术选型 |
|------|----------|
| 前端框架 | React 18 + TypeScript + Vite |
| 状态管理 | Redux Toolkit + RTK Query |
| UI 组件库 | Fluent UI React v9 |
| 后端 | Python 3.11 + FastAPI + Uvicorn |
| 数据库 | Azure Cosmos DB (NoSQL) |
| 文件存储 | Azure Blob Storage |
| AI模型 | Azure OpenAI Service |
| 密钥管理 | Azure Key Vault |
| 部署 | Azure App Service (Web App for Containers) |
| 容器化 | Docker + Docker Compose |
| 认证 | JWT (简单用户名密码) |

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         Azure Cloud                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ App Service  │  │ App Service  │  │   Azure OpenAI       │  │
│  │ (Frontend)   │  │ (Backend)    │  │   Service            │  │
│  │ React SPA    │  │ FastAPI      │  │   - GPT-4o           │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │              │
│         │    REST API     │      API Calls       │              │
│         └────────────────►│◄─────────────────────┘              │
│                           │                                      │
│         ┌─────────────────┼─────────────────┐                   │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Cosmos DB    │  │ Blob Storage │  │ Key Vault    │          │
│  │ - Users      │  │ - Files      │  │ - API Keys   │          │
│  │ - Chats      │  │ - Images     │  │ - Secrets    │          │
│  │ - Messages   │  │              │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Azure OpenAI 模型推荐

### 推荐配置

| 用途 | 模型 | 理由 |
|------|------|------|
| **主要对话** | GPT-4o | 性价比最高，支持文本+图片，响应快 |
| **备选经济** | GPT-4o-mini | 成本更低，适合简单对话 |
| **文档分析** | GPT-4o (Vision) | 同一模型支持图片理解 |

### Azure OpenAI 部署配置建议

```yaml
模型部署:
  名称: gpt-4o-deployment
  模型: gpt-4o
  版本: 2024-08-06 (最新稳定版)
  容量: 10K TPM (tokens per minute) 起步
  
定价参考 (East US):
  输入: $2.50 / 1M tokens
  输出: $10.00 / 1M tokens
  
建议区域: East US 或 Sweden Central (模型可用性最好)
```

## 数据模型设计

### Cosmos DB 容器结构

```typescript
// 用户容器 (users)
interface User {
  id: string;              // 用户ID (partition key)
  email: string;           // 邮箱
  username: string;        // 用户名
  passwordHash: string;    // 密码哈希
  createdAt: string;       // 创建时间
  settings: {
    defaultModel: string;
    theme: 'light' | 'dark';
  };
}

// 会话容器 (conversations)
interface Conversation {
  id: string;              // 会话ID
  userId: string;          // 用户ID (partition key)
  title: string;           // 会话标题
  systemPrompt: string;    // 自定义系统提示
  model: string;           // 使用的模型
  createdAt: string;
  updatedAt: string;
  messageCount: number;
}

// 消息容器 (messages)
interface Message {
  id: string;              // 消息ID
  conversationId: string;  // 会话ID (partition key)
  role: 'user' | 'assistant' | 'system';
  content: string;
  attachments?: Attachment[];
  tokens?: {
    input: number;
    output: number;
  };
  createdAt: string;
}

// 附件类型
interface Attachment {
  id: string;
  type: 'image' | 'file';
  fileName: string;
  blobUrl: string;
  mimeType: string;
  size: number;
}
```

## 项目目录结构

```
ai-chat/
├── frontend/                    # React 前端
│   ├── src/
│   │   ├── components/         # UI 组件 (Fluent UI)
│   │   │   ├── Chat/
│   │   │   ├── Sidebar/
│   │   │   ├── Auth/
│   │   │   └── Layout/
│   │   ├── features/           # Redux Toolkit Slices
│   │   ├── services/           # RTK Query API
│   │   ├── store/              # Redux Store 配置
│   │   ├── hooks/              # 自定义 Hooks
│   │   ├── types/              # TypeScript 类型
│   │   ├── styles/             # Fluent UI 主题
│   │   └── utils/              # 工具函数
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── api/                # API 路由
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── conversations.py
│   │   │   └── files.py
│   │   ├── core/               # 核心配置
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── dependencies.py
│   │   ├── models/             # 数据模型
│   │   ├── services/           # 业务逻辑
│   │   │   ├── azure_openai.py
│   │   │   ├── cosmos_db.py
│   │   │   └── blob_storage.py
│   │   └── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
│
├── docker-compose.yml           # 本地开发
├── docker-compose.prod.yml      # 生产配置
├── .env.example                 # 环境变量模板
├── .gitignore
└── README.md
```

## API 接口设计

### 认证相关

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/refresh` | 刷新Token |
| GET | `/api/auth/me` | 获取当前用户 |

### 会话管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/conversations` | 获取会话列表 |
| POST | `/api/conversations` | 创建新会话 |
| GET | `/api/conversations/{id}` | 获取会话详情 |
| PUT | `/api/conversations/{id}` | 更新会话 |
| DELETE | `/api/conversations/{id}` | 删除会话 |

### 聊天相关

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/conversations/{id}/messages` | 获取消息历史 |
| POST | `/api/conversations/{id}/messages` | 发送消息 |
| POST | `/api/conversations/{id}/messages/stream` | 流式发送消息 |

### 文件上传

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/files/upload` | 上传文件 |
| GET | `/api/files/{id}` | 获取文件信息 |
| DELETE | `/api/files/{id}` | 删除文件 |

## 开发阶段划分

### 第一阶段：基础架构 (预计 3-4 天)
- [ ] 项目初始化与目录结构搭建
- [ ] Docker 和 Docker Compose 配置
- [ ] Azure 资源创建脚本
- [ ] 环境配置管理

### 第二阶段：后端核心 (预计 5-6 天)
- [ ] FastAPI 项目搭建
- [ ] Cosmos DB 连接与数据模型
- [ ] 用户认证系统 (JWT)
- [ ] 会话 CRUD API
- [ ] Azure OpenAI 集成
- [ ] 流式响应实现

### 第三阶段：文件处理 (预计 2-3 天)
- [ ] Azure Blob Storage 集成
- [ ] 文件上传 API
- [ ] 图片预处理
- [ ] GPT-4o Vision 集成

### 第四阶段：前端开发 (预计 5-7 天)
- [ ] React 项目搭建
- [ ] 登录/注册页面
- [ ] 聊天界面组件
- [ ] 会话侧边栏
- [ ] 消息渲染 (Markdown支持)
- [ ] 文件上传组件
- [ ] 流式消息显示

### 第五阶段：集成与优化 (预计 2-3 天)
- [ ] 前后端集成测试
- [ ] 错误处理完善
- [ ] 性能优化
- [ ] 安全审查

### 第六阶段：部署 (预计 2-3 天)
- [ ] Azure 资源正式部署
- [ ] CI/CD 流水线 (可选)
- [ ] 域名与 SSL 配置
- [ ] 监控告警配置

## Azure 资源清单

| 资源 | SKU/配置 | 预估月成本 |
|------|----------|-----------|
| App Service Plan | B1 (Frontend) | $13 |
| App Service Plan | B1 (Backend) | $13 |
| Cosmos DB | Serverless | $5-30 (按使用) |
| Blob Storage | Hot tier | $2-5 |
| Azure OpenAI | GPT-4o | $10-50 (按使用) |
| Key Vault | Standard | $0.03/操作 |
| **总计** | | **约 $45-120/月** |

## 环境变量配置

环境变量分为两类，详见 [`docs/env-config.md`](env-config.md)：

### 🔐 敏感密钥 (必须存入 Azure Key Vault)

| 变量名 | 说明 |
|--------|------|
| `AZURE_OPENAI_API_KEY` | Azure OpenAI 服务密钥 |
| `COSMOS_DB_KEY` | Cosmos DB 主密钥 |
| `AZURE_STORAGE_CONNECTION_STRING` | Blob Storage 连接字符串 |
| `JWT_SECRET_KEY` | JWT 签名密钥 |

### ⚙️ 配置项 (App Service 直接配置)

| 变量名 | 示例值 |
|--------|--------|
| `AZURE_OPENAI_ENDPOINT` | `https://aoai-ai-chat.openai.azure.com/` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | `gpt-4o` |
| `COSMOS_DB_ENDPOINT` | `https://cosmos-ai-chat.documents.azure.com:443/` |
| `COSMOS_DB_DATABASE_NAME` | `ai-chat-db` |
| `CORS_ORIGINS` | `https://your-frontend.azurewebsites.net` |

### 🛠️ 本地开发

本地开发时，所有变量放在 `.env.local` 文件中（已加入 .gitignore）。

## 下一步行动

准备就绪后，请切换到 **Code 模式** 开始实现。建议从以下顺序开始：

1. 创建项目基础结构
2. 配置 Docker 开发环境
3. 实现后端 API
4. 开发前端界面
5. 部署到 Azure

---

*文档创建时间: 2024-12-17*
*状态: 待审核*