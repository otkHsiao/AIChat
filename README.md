# AI Chat Application 🤖💬

一个类似 ChatGPT 的智能聊天应用，基于 Azure OpenAI 构建，支持流式响应、多轮对话、文件上传等功能。

## ✨ 功能特点

- 🔄 **流式响应** - 实时显示 AI 回复，提升用户体验
- 💬 **多轮对话** - 支持上下文记忆的连续对话
- 📁 **文件上传** - 支持图片和文档上传分析
- 🎨 **现代 UI** - 基于 Fluent UI v9 的美观界面
- 🌙 **深色模式** - 支持浅色/深色主题切换
- 🔐 **用户认证** - JWT 身份验证和授权
- 📱 **响应式设计** - 适配桌面和移动设备

## 🛠️ 技术栈

### 后端
- **Python 3.11+** - 编程语言
- **FastAPI** - 高性能 Web 框架
- **Azure OpenAI** - GPT-4o 模型
- **Azure Cosmos DB** - NoSQL 数据库
- **Azure Blob Storage** - 文件存储
- **JWT** - 身份认证

### 前端
- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Redux Toolkit** - 状态管理
- **RTK Query** - 数据获取和缓存
- **Fluent UI v9** - 微软设计系统
- **Vite** - 构建工具

### 基础设施
- **Docker** - 容器化
- **Azure App Service** - 托管平台
- **Azure Key Vault** - 密钥管理

## 📁 项目结构

```
chat-app/
├── backend/                 # 后端 FastAPI 应用
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心配置
│   │   ├── schemas/        # Pydantic 模型
│   │   └── services/       # 业务逻辑
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # 前端 React 应用
│   ├── src/
│   │   ├── components/     # UI 组件
│   │   ├── features/       # Redux slices
│   │   ├── hooks/          # 自定义 hooks
│   │   ├── pages/          # 页面组件
│   │   ├── services/       # API 服务
│   │   └── types/          # TypeScript 类型
│   ├── Dockerfile
│   └── package.json
├── docs/                   # 项目文档
│   ├── architecture.md     # 架构设计
│   ├── api-spec.md         # API 规范
│   ├── azure-setup.md      # Azure 配置指南
│   └── env-config.md       # 环境变量说明
├── docker-compose.yml      # Docker 编排
└── README.md
```

## 🚀 快速开始

### 前置条件

- Node.js 20+
- Python 3.11+
- Docker & Docker Compose
- Azure 账户 (用于 Azure OpenAI、Cosmos DB、Blob Storage)

### 1. 克隆项目

```bash
git clone <repository-url>
cd chat-app
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env.local

# 编辑 .env.local 填入你的 Azure 资源信息
```

### 3. Azure 资源配置

参考 [Azure 配置指南](./docs/azure-setup.md) 创建所需的 Azure 资源：
- Azure OpenAI (GPT-4o 部署)
- Azure Cosmos DB (Serverless)
- Azure Blob Storage

### 4. 本地开发

**使用 Docker Compose (推荐):**

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

**手动启动:**

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端 (新终端)
cd frontend
npm install
npm run dev
```

### 5. 访问应用

- 前端: http://localhost:5173 (开发) 或 http://localhost:3000 (Docker)
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 📖 API 文档

详细的 API 规范请参考 [API 文档](./docs/api-spec.md)。

主要端点：

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| GET | `/api/conversations` | 获取对话列表 |
| POST | `/api/conversations` | 创建新对话 |
| POST | `/api/chat/{id}/stream` | 发送消息(流式) |
| POST | `/api/files/upload` | 上传文件 |

## 🔧 配置说明

### 环境变量

| 变量名 | 描述 | 必需 |
|--------|------|------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI 端点 | ✅ |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API 密钥 | ✅ |
| `COSMOS_DB_ENDPOINT` | Cosmos DB 端点 | ✅ |
| `COSMOS_DB_KEY` | Cosmos DB 密钥 | ✅ |
| `JWT_SECRET_KEY` | JWT 签名密钥 | ✅ |

更多配置选项请参考 [环境变量文档](./docs/env-config.md)。

## 🚢 部署

### Azure App Service

```bash
# 构建 Docker 镜像
docker build -t chat-backend ./backend
docker build -t chat-frontend ./frontend

# 推送到 Azure Container Registry
az acr login --name <registry-name>
docker tag chat-backend <registry-name>.azurecr.io/chat-backend:latest
docker tag chat-frontend <registry-name>.azurecr.io/chat-frontend:latest
docker push <registry-name>.azurecr.io/chat-backend:latest
docker push <registry-name>.azurecr.io/chat-frontend:latest

# 部署到 App Service
az webapp create --resource-group <rg-name> --plan <plan-name> \
  --name <app-name> --deployment-container-image-name <registry-name>.azurecr.io/chat-backend:latest
```

详细部署步骤请参考 [Azure 配置指南](./docs/azure-setup.md)。

## 🧪 测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm test
```

## 📝 开发指南

### 代码风格

- 后端: 遵循 PEP 8，使用 Black 格式化
- 前端: 遵循 ESLint 配置，使用 Prettier 格式化

### 提交规范

使用 Conventional Commits:
- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `style:` 代码格式化
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具相关

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**Made with ❤️ using Azure AI**