# AI Chat 项目开发待办清单

## 第一阶段：基础架构搭建 ✅ 已完成

### 1.1 项目初始化
- [x] 创建项目根目录结构
- [x] 创建 `.gitignore` 文件
- [x] 创建 `.env.example` 环境变量模板
- [x] 创建 `README.md` 项目说明文档

### 1.2 后端项目初始化
- [x] 创建 `backend/` 目录结构
- [x] 创建 `backend/requirements.txt` 依赖文件
- [x] 创建 `backend/pyproject.toml` 项目配置
- [x] 创建 `backend/app/main.py` FastAPI 入口
- [x] 创建 `backend/app/core/config.py` 配置管理

### 1.3 前端项目初始化
- [x] 使用 Vite 创建 React + TypeScript 项目
- [x] 配置 ESLint 和 Prettier (package.json)
- [x] 安装核心依赖:
  - [x] @reduxjs/toolkit (状态管理)
  - [x] react-redux (React Redux 绑定)
  - [x] @fluentui/react-components (Fluent UI v9)
  - [x] @fluentui/react-icons (图标库)
  - [x] react-router-dom (路由)
  - [x] axios (HTTP 客户端)
- [x] 配置路径别名 (@/)
- [x] 创建基础目录结构 (features/, services/, store/)

### 1.4 Docker 配置
- [x] 创建 `backend/Dockerfile`
- [x] 创建 `frontend/Dockerfile`
- [x] 创建 `frontend/nginx.conf` Nginx 配置
- [x] 创建 `docker-compose.yml` 本地开发配置
- [x] 创建 `docker-compose.dev.yml` 开发配置
- [ ] 测试 Docker Compose 本地启动

---

## 第二阶段：后端核心开发 ✅ 已完成

### 2.1 数据库连接
- [x] 创建 `backend/app/services/cosmos_db.py` Cosmos DB 服务
- [x] 实现数据库连接池管理
- [x] 创建数据库初始化脚本
- [x] 创建容器 (users, conversations, messages)

### 2.2 数据模型定义
- [x] 创建 Pydantic schemas 用于请求/响应验证
  - [x] `backend/app/schemas/auth.py`
  - [x] `backend/app/schemas/conversation.py`
  - [x] `backend/app/schemas/message.py`
  - [x] `backend/app/schemas/file.py`
  - [x] `backend/app/schemas/common.py`

### 2.3 用户认证系统
- [x] 创建 `backend/app/core/security.py` 安全工具
- [x] 实现密码哈希 (bcrypt)
- [x] 实现 JWT Token 生成和验证
- [x] 创建 `backend/app/api/auth.py` 认证路由
- [x] 实现用户注册 API
- [x] 实现用户登录 API
- [x] 实现 Token 刷新 API
- [x] 实现获取当前用户 API
- [x] 创建认证依赖注入

### 2.4 会话管理 API
- [x] 创建 `backend/app/api/conversations.py` 会话路由
- [x] 实现创建会话 API
- [x] 实现获取会话列表 API
- [x] 实现获取单个会话 API
- [x] 实现更新会话 API (标题、系统提示)
- [x] 实现删除会话 API

### 2.5 Azure OpenAI 集成
- [x] 创建 `backend/app/services/azure_openai.py` OpenAI 服务
- [x] 实现基础聊天完成调用
- [x] 实现流式响应 (SSE)
- [x] 实现带图片的多模态调用
- [x] 实现 Token 计数
- [x] 添加错误处理和重试机制

### 2.6 聊天 API
- [x] 创建 `backend/app/api/chat.py` 聊天路由
- [x] 实现获取消息历史 API
- [x] 实现发送消息 API (非流式)
- [x] 实现流式发送消息 API (SSE)
- [x] 实现消息上下文管理 (限制历史长度)

---

## 第三阶段：文件处理 ✅ 已完成

### 3.1 Blob Storage 集成
- [x] 创建 `backend/app/services/blob_storage.py` 存储服务
- [x] 实现文件上传功能
- [x] 实现生成 SAS URL
- [x] 实现文件删除功能
- [x] 配置文件类型和大小限制

### 3.2 文件上传 API
- [x] 创建 `backend/app/api/files.py` 文件路由
- [x] 实现文件上传 API (支持多文件)
- [x] 实现图片压缩/调整大小
- [x] 实现获取文件信息 API
- [x] 实现删除文件 API

### 3.3 多模态消息支持
- [x] 修改消息模型支持附件
- [x] 实现图片消息发送 (GPT-4o Vision)

---

## 第四阶段：前端开发 ✅ 已完成

### 4.1 Redux Store 基础设施
- [x] 配置 Redux Store (`store/index.ts`)
- [x] 配置 RTK Query 基础 API (`services/api.ts`)
- [x] 创建类型化 Hooks (`useAppDispatch`, `useAppSelector`)
- [x] 配置 Redux DevTools

### 4.2 Fluent UI 配置
- [x] 配置 FluentProvider 和主题
- [x] 创建自定义主题 (`theme/index.ts`)
- [x] 配置暗色/亮色主题切换
- [x] 创建全局样式 (`index.css`)

### 4.3 Redux Feature Slices
- [x] 创建 authSlice (认证状态)
- [x] 创建 chatSlice (聊天状态)
- [x] 创建 conversationsSlice (会话状态)
- [x] 创建 uiSlice (UI 状态：侧边栏、主题等)
- [x] 创建对应的 Selectors

### 4.4 RTK Query API 服务
- [x] 创建 authApi (登录/注册/刷新)
- [x] 创建 conversationsApi (会话 CRUD)
- [x] 创建 chatApi (消息历史)
- [x] 创建 filesApi (文件上传)
- [x] 配置自动 Token 注入

### 4.5 路由配置
- [x] 创建路由配置 (`App.tsx`)
- [x] 创建受保护路由组件 (RequireAuth)
- [x] 实现路由守卫逻辑

### 4.6 认证页面 (Fluent UI)
- [x] 创建登录页面 (`LoginPage.tsx`)
- [x] 创建注册页面 (`RegisterPage.tsx`)
- [x] 实现表单验证
- [x] 连接 authApi 和 authSlice

### 4.7 主布局 (Fluent UI)
- [x] 创建 AppLayout 组件
- [x] 创建顶部导航栏 (Header)
- [x] 实现响应式侧边栏

### 4.8 会话侧边栏 (Fluent UI)
- [x] 创建 Sidebar 组件
- [x] 创建会话列表 (`ConversationList.tsx`)
- [x] 实现新建会话按钮
- [x] 实现会话项
- [x] 实现会话删除

### 4.9 聊天界面 (Fluent UI)
- [x] 创建 ChatContainer 组件
- [x] 创建消息列表组件 (`MessageList.tsx`)
- [x] 创建消息气泡组件 (`MessageItem.tsx`)
- [x] 实现 Markdown 渲染
- [x] 实现代码高亮

### 4.10 输入区域 (Fluent UI)
- [x] 创建消息输入组件 (`MessageInput.tsx`)
- [x] 实现自动调整高度
- [x] 实现发送按钮
- [x] 实现快捷键发送
- [x] 创建文件上传按钮
- [x] 实现文件预览

### 4.11 流式消息
- [x] 创建 useStreamingChat Hook
- [x] 实现 SSE 连接管理
- [x] 实现打字机效果
- [x] 实现流式消息中断 (AbortController)

### 4.12 设置功能 (Fluent UI)
- [x] 创建设置 Dialog (`SettingsDialog.tsx`)
- [x] 实现模型选择
- [x] 实现主题选择

---

## 第五阶段：集成与优化 🔄 进行中

### 5.1 前后端集成
- [x] 配置 CORS
- [ ] 测试所有 API 端点
- [ ] 处理错误响应显示
- [ ] 实现全局错误边界

### 5.2 性能优化
- [ ] 实现消息虚拟滚动 (大量消息)
- [ ] 实现图片懒加载
- [ ] 优化重新渲染
- [ ] 添加请求缓存

### 5.3 用户体验
- [ ] 添加加载骨架屏
- [ ] 添加操作成功/失败提示
- [ ] 实现离线状态提示
- [ ] 优化移动端体验

### 5.4 安全加固
- [ ] 实现请求速率限制
- [ ] 添加输入清理
- [ ] 实现 XSS 防护
- [ ] 审查敏感数据处理

---

## 第六阶段：部署 ⬜ 待开始

### 6.1 Azure 资源创建
- [ ] 创建资源组
- [ ] 创建 Azure OpenAI 资源并部署 GPT-4o 模型
- [ ] 创建 Cosmos DB 账户
- [ ] 创建 Storage Account
- [ ] 创建 Key Vault
- [ ] 创建 App Service Plan
- [ ] 创建前端 Web App
- [ ] 创建后端 Web App

### 6.2 配置与部署
- [ ] 配置 Key Vault 密钥
- [ ] 配置 App Service 环境变量
- [ ] 推送 Docker 镜像到 Azure Container Registry
- [ ] 部署前端应用
- [ ] 部署后端应用
- [ ] 配置自定义域名 (可选)
- [ ] 配置 SSL 证书

### 6.3 监控与维护
- [ ] 配置 Application Insights
- [ ] 设置告警规则
- [ ] 创建运维文档

---

## 注意事项

1. **安全性**：所有密钥必须存储在 Key Vault，禁止硬编码
2. **成本控制**：使用 Serverless Cosmos DB，按需扩展
3. **代码质量**：遵循 Python/TypeScript 最佳实践
4. **测试**：关键功能需要单元测试

---

## 进度追踪

| 阶段 | 状态 | 预计时间 | 实际时间 |
|------|------|---------|---------|
| 基础架构 | ✅ 已完成 | 3-4 天 | 1 天 |
| 后端核心 | ✅ 已完成 | 5-6 天 | 1 天 |
| 文件处理 | ✅ 已完成 | 2-3 天 | 1 天 |
| 前端开发 | ✅ 已完成 | 5-7 天 | 1 天 |
| 集成优化 | 🔄 进行中 | 2-3 天 | - |
| 部署上线 | ⬜ 待开始 | 2-3 天 | - |

**总预计时间：19-26 天**
**实际已用时间：~4 天（代码框架）**

---

## 下一步行动

1. **安装依赖并测试运行**
   ```bash
   # 后端
   cd backend
   pip install -r requirements.txt
   
   # 前端
   cd frontend
   npm install
   ```

2. **配置环境变量**
   - 复制 `.env.example` 到 `.env.local`
   - 填入 Azure 资源连接信息

3. **本地测试**
   ```bash
   # 使用 Docker Compose
   docker-compose up -d
   ```

4. **修复任何运行时错误**

---

*最后更新：2024-12-17*