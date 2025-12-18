# Azure 部署指南

本文档介绍如何将 AI Chat 应用部署到 Azure。

## 先决条件

1. **Azure CLI** - 已安装并登录
   ```bash
   az login
   ```

2. **Docker** - 已安装并运行

3. **Azure 订阅** - 有足够的权限创建资源

## 已创建的 Azure 资源

在部署应用之前，以下资源已经创建：

| 资源类型 | 名称 | 区域 | 用途 |
|---------|------|------|------|
| Azure OpenAI | aoai-ai-chat-xc | East US | GPT-4o 模型 |
| Cosmos DB | cosmosaichatxc | West US 2 | 数据存储 |
| Storage Account | stgaichatxc | East Asia | 文件存储 |

## 部署步骤

### 方法 1: 使用自动化脚本

#### Windows (PowerShell)
```powershell
cd deploy
.\azure-deploy.ps1
```

#### Linux/macOS (Bash)
```bash
cd deploy
chmod +x azure-deploy.sh
./azure-deploy.sh
```

### 方法 2: 手动部署

#### 1. 创建 Azure Container Registry

```bash
# 设置变量
RESOURCE_GROUP="rg-ai-chat"
LOCATION="eastasia"
ACR_NAME="acraichat$(date +%s)"

# 创建 ACR
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --admin-enabled true
```

#### 2. 构建并推送 Docker 镜像

```bash
# 登录 ACR
az acr login --name $ACR_NAME

# 获取 ACR 地址
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)

# 构建后端镜像
docker build -t $ACR_LOGIN_SERVER/ai-chat-backend:latest ./backend
docker push $ACR_LOGIN_SERVER/ai-chat-backend:latest

# 构建前端镜像
docker build -t $ACR_LOGIN_SERVER/ai-chat-frontend:latest ./frontend
docker push $ACR_LOGIN_SERVER/ai-chat-frontend:latest
```

#### 3. 创建 App Service Plan

```bash
APP_SERVICE_PLAN="asp-ai-chat"

az appservice plan create \
    --name $APP_SERVICE_PLAN \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --is-linux \
    --sku B1
```

#### 4. 部署后端 Web App

```bash
BACKEND_APP_NAME="api-ai-chat-$(date +%s)"

az webapp create \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_SERVICE_PLAN \
    --deployment-container-image-name $ACR_LOGIN_SERVER/ai-chat-backend:latest

# 配置容器注册表凭据
az webapp config container set \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --docker-registry-server-url https://$ACR_LOGIN_SERVER \
    --docker-registry-server-user $(az acr credential show --name $ACR_NAME --query username -o tsv) \
    --docker-registry-server-password $(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)
```

#### 5. 配置后端环境变量

```bash
az webapp config appsettings set \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
    AZURE_OPENAI_ENDPOINT="https://aoai-ai-chat-xc.openai.azure.com/" \
    AZURE_OPENAI_API_KEY="<your-api-key>" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o" \
    AZURE_OPENAI_API_VERSION="2024-02-15-preview" \
    COSMOS_DB_ENDPOINT="https://cosmosaichatxc.documents.azure.com:443/" \
    COSMOS_DB_KEY="<your-cosmos-key>" \
    COSMOS_DB_DATABASE_NAME="chatdb" \
    AZURE_STORAGE_CONNECTION_STRING="<your-storage-connection>" \
    AZURE_STORAGE_CONTAINER_NAME="uploads" \
    JWT_SECRET_KEY="<your-jwt-secret>" \
    CORS_ORIGINS="https://<frontend-app>.azurewebsites.net"
```

#### 6. 部署前端 Web App

```bash
FRONTEND_APP_NAME="web-ai-chat-$(date +%s)"
BACKEND_URL="https://$BACKEND_APP_NAME.azurewebsites.net"

az webapp create \
    --name $FRONTEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_SERVICE_PLAN \
    --deployment-container-image-name $ACR_LOGIN_SERVER/ai-chat-frontend:latest

# 配置容器和 API URL
az webapp config container set \
    --name $FRONTEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --docker-registry-server-url https://$ACR_LOGIN_SERVER \
    --docker-registry-server-user $(az acr credential show --name $ACR_NAME --query username -o tsv) \
    --docker-registry-server-password $(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

az webapp config appsettings set \
    --name $FRONTEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings API_URL=$BACKEND_URL
```

## 环境变量说明

### 后端环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| AZURE_OPENAI_ENDPOINT | Azure OpenAI 端点 | https://xxx.openai.azure.com/ |
| AZURE_OPENAI_API_KEY | Azure OpenAI API 密钥 | xxx |
| AZURE_OPENAI_DEPLOYMENT_NAME | 部署名称 | gpt-4o |
| AZURE_OPENAI_API_VERSION | API 版本 | 2024-02-15-preview |
| COSMOS_DB_ENDPOINT | Cosmos DB 端点 | https://xxx.documents.azure.com:443/ |
| COSMOS_DB_KEY | Cosmos DB 密钥 | xxx |
| COSMOS_DB_DATABASE_NAME | 数据库名称 | chatdb |
| AZURE_STORAGE_CONNECTION_STRING | 存储账户连接字符串 | xxx |
| AZURE_STORAGE_CONTAINER_NAME | Blob 容器名称 | uploads |
| JWT_SECRET_KEY | JWT 签名密钥 | 随机安全字符串 |
| CORS_ORIGINS | 允许的 CORS 来源 | https://xxx.azurewebsites.net |

### 前端环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| API_URL | 后端 API 地址 | https://api-xxx.azurewebsites.net |

## 更新部署

### 更新后端

```bash
# 重新构建并推送镜像
docker build -t $ACR_LOGIN_SERVER/ai-chat-backend:latest ./backend
docker push $ACR_LOGIN_SERVER/ai-chat-backend:latest

# 重启 Web App 以拉取新镜像
az webapp restart --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP
```

### 更新前端

```bash
# 重新构建并推送镜像
docker build -t $ACR_LOGIN_SERVER/ai-chat-frontend:latest ./frontend
docker push $ACR_LOGIN_SERVER/ai-chat-frontend:latest

# 重启 Web App 以拉取新镜像
az webapp restart --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP
```

## 监控和日志

### 查看容器日志

```bash
# 后端日志
az webapp log tail --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP

# 前端日志
az webapp log tail --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP
```

### 启用应用程序日志

```bash
az webapp log config \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --docker-container-logging filesystem
```

## 故障排除

### 容器无法启动

1. 检查容器日志：
   ```bash
   az webapp log tail --name <app-name> --resource-group $RESOURCE_GROUP
   ```

2. 验证环境变量配置

3. 确保 ACR 凭据正确

### 前端无法连接后端

1. 检查 CORS_ORIGINS 配置是否包含前端 URL
2. 验证 API_URL 环境变量
3. 检查后端健康状态：访问 `https://<backend>/health`

### 数据库连接失败

1. 验证 COSMOS_DB_ENDPOINT 和 COSMOS_DB_KEY
2. 检查 Cosmos DB 防火墙设置（允许 Azure 服务访问）

## 成本优化

- 使用 **B1** App Service 计划（适合开发/测试）
- 使用 **Serverless** Cosmos DB（按使用量计费）
- 使用 **Basic** ACR SKU

## 安全建议

1. 使用 Azure Key Vault 存储敏感配置
2. 启用 HTTPS（App Service 默认启用）
3. 配置 IP 限制（如需要）
4. 定期轮换 API 密钥和连接字符串