# Azure 资源部署指南

## 资源清单

| 资源类型 | 名称建议 | SKU | 用途 |
|----------|----------|-----|------|
| Resource Group | rg-ai-chat | - | 资源容器 |
| Azure OpenAI | aoai-ai-chat | S0 | AI 模型服务 |
| Cosmos DB | cosmos-ai-chat | Serverless | 数据存储 |
| Storage Account | stgaichat | Standard LRS | 文件存储 |
| Key Vault | kv-ai-chat | Standard | 密钥管理 |
| App Service Plan | asp-ai-chat | B1 | 应用托管 |
| Web App - Frontend | app-ai-chat-fe | - | 前端应用 |
| Web App - Backend | app-ai-chat-be | - | 后端应用 |
| Container Registry | acraichat | Basic | 镜像仓库 |

## 部署步骤

### 1. 创建资源组

```bash
# 登录 Azure
az login

# 设置订阅 (如果有多个)
az account set --subscription "Your-Subscription-Name"

# 创建资源组
az group create \
  --name rg-ai-chat \
  --location eastus
```

### 2. 创建 Azure OpenAI 资源

```bash
# 创建 OpenAI 资源
az cognitiveservices account create \
  --name aoai-ai-chat \
  --resource-group rg-ai-chat \
  --kind OpenAI \
  --sku S0 \
  --location eastus \
  --yes
```

#### 部署 GPT-4o 模型

通过 Azure Portal 操作：

1. 进入 Azure Portal > Azure OpenAI 资源
2. 点击 **Model deployments** > **Manage Deployments**
3. 点击 **+ Create new deployment**
4. 配置：
   - Deployment name: `gpt-4o`
   - Model: `gpt-4o`
   - Model version: `2024-08-06` (最新稳定版)
   - Tokens per Minute Rate Limit: `10000` (根据需要调整)

或使用 CLI：

```bash
# 部署模型
az cognitiveservices account deployment create \
  --name aoai-ai-chat \
  --resource-group rg-ai-chat \
  --deployment-name gpt-4o \
  --model-name gpt-4o \
  --model-version "2024-08-06" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard
```

### 3. 创建 Cosmos DB

```bash
# 创建 Cosmos DB 账户 (Serverless)
az cosmosdb create \
  --name cosmos-ai-chat \
  --resource-group rg-ai-chat \
  --locations regionName=eastus \
  --capabilities EnableServerless

# 创建数据库
az cosmosdb sql database create \
  --account-name cosmos-ai-chat \
  --resource-group rg-ai-chat \
  --name ai-chat-db

# 创建容器 - users
az cosmosdb sql container create \
  --account-name cosmos-ai-chat \
  --resource-group rg-ai-chat \
  --database-name ai-chat-db \
  --name users \
  --partition-key-path "/id"

# 创建容器 - conversations
az cosmosdb sql container create \
  --account-name cosmos-ai-chat \
  --resource-group rg-ai-chat \
  --database-name ai-chat-db \
  --name conversations \
  --partition-key-path "/userId"

# 创建容器 - messages
az cosmosdb sql container create \
  --account-name cosmos-ai-chat \
  --resource-group rg-ai-chat \
  --database-name ai-chat-db \
  --name messages \
  --partition-key-path "/conversationId"
```

### 4. 创建 Storage Account

```bash
# 创建存储账户
az storage account create \
  --name stgaichat \
  --resource-group rg-ai-chat \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2

# 创建 Blob 容器
az storage container create \
  --name uploads \
  --account-name stgaichat \
  --public-access off
```

### 5. 创建 Key Vault

```bash
# 创建 Key Vault
az keyvault create \
  --name kv-ai-chat \
  --resource-group rg-ai-chat \
  --location eastus

# 获取 OpenAI API Key 并存储
OPENAI_KEY=$(az cognitiveservices account keys list \
  --name aoai-ai-chat \
  --resource-group rg-ai-chat \
  --query key1 -o tsv)

az keyvault secret set \
  --vault-name kv-ai-chat \
  --name azure-openai-api-key \
  --value "$OPENAI_KEY"

# 获取 Cosmos DB Key 并存储
COSMOS_KEY=$(az cosmosdb keys list \
  --name cosmos-ai-chat \
  --resource-group rg-ai-chat \
  --query primaryMasterKey -o tsv)

az keyvault secret set \
  --vault-name kv-ai-chat \
  --name cosmos-db-key \
  --value "$COSMOS_KEY"

# 获取 Storage 连接字符串并存储
STORAGE_CONN=$(az storage account show-connection-string \
  --name stgaichat \
  --resource-group rg-ai-chat \
  --query connectionString -o tsv)

az keyvault secret set \
  --vault-name kv-ai-chat \
  --name storage-connection-string \
  --value "$STORAGE_CONN"
```

### 6. 创建容器注册表

```bash
# 创建 Container Registry
az acr create \
  --name acraichat \
  --resource-group rg-ai-chat \
  --sku Basic \
  --admin-enabled true
```

### 7. 创建 App Service

```bash
# 创建 App Service Plan
az appservice plan create \
  --name asp-ai-chat \
  --resource-group rg-ai-chat \
  --is-linux \
  --sku B1

# 创建前端 Web App
az webapp create \
  --name app-ai-chat-fe \
  --resource-group rg-ai-chat \
  --plan asp-ai-chat \
  --deployment-container-image-name nginx:alpine

# 创建后端 Web App
az webapp create \
  --name app-ai-chat-be \
  --resource-group rg-ai-chat \
  --plan asp-ai-chat \
  --deployment-container-image-name python:3.11-slim
```

### 8. 配置 Web App 环境变量

```bash
# 后端环境变量
az webapp config appsettings set \
  --name app-ai-chat-be \
  --resource-group rg-ai-chat \
  --settings \
    AZURE_OPENAI_ENDPOINT="https://aoai-ai-chat.openai.azure.com/" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o" \
    AZURE_OPENAI_API_VERSION="2024-08-06" \
    COSMOS_DB_ENDPOINT="https://cosmos-ai-chat.documents.azure.com:443/" \
    COSMOS_DB_DATABASE_NAME="ai-chat-db" \
    AZURE_STORAGE_CONTAINER_NAME="uploads" \
    CORS_ORIGINS="https://app-ai-chat-fe.azurewebsites.net"

# 配置 Key Vault 引用
az webapp config appsettings set \
  --name app-ai-chat-be \
  --resource-group rg-ai-chat \
  --settings \
    AZURE_OPENAI_API_KEY="@Microsoft.KeyVault(VaultName=kv-ai-chat;SecretName=azure-openai-api-key)" \
    COSMOS_DB_KEY="@Microsoft.KeyVault(VaultName=kv-ai-chat;SecretName=cosmos-db-key)" \
    AZURE_STORAGE_CONNECTION_STRING="@Microsoft.KeyVault(VaultName=kv-ai-chat;SecretName=storage-connection-string)"

# 前端环境变量
az webapp config appsettings set \
  --name app-ai-chat-fe \
  --resource-group rg-ai-chat \
  --settings \
    VITE_API_BASE_URL="https://app-ai-chat-be.azurewebsites.net"
```

### 9. 配置 Managed Identity

```bash
# 为后端启用系统托管标识
az webapp identity assign \
  --name app-ai-chat-be \
  --resource-group rg-ai-chat

# 获取 Principal ID
PRINCIPAL_ID=$(az webapp identity show \
  --name app-ai-chat-be \
  --resource-group rg-ai-chat \
  --query principalId -o tsv)

# 授权访问 Key Vault
az keyvault set-policy \
  --name kv-ai-chat \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get list
```

## 成本估算

| 资源 | SKU | 预估月成本 (USD) |
|------|-----|-----------------|
| App Service Plan | B1 | $13.14 |
| Cosmos DB | Serverless | $5 - $30 |
| Storage Account | Standard LRS | $2 - $5 |
| Azure OpenAI | Pay-as-you-go | $10 - $50 |
| Key Vault | Standard | < $1 |
| Container Registry | Basic | $5 |
| **总计** | | **$35 - $105** |

## 资源清理

```bash
# 删除整个资源组 (包含所有资源)
az group delete --name rg-ai-chat --yes --no-wait
```

## 重要链接

部署完成后，记录以下信息：

| 项目 | 值 |
|------|-----|
| 前端 URL | https://app-ai-chat-fe.azurewebsites.net |
| 后端 URL | https://app-ai-chat-be.azurewebsites.net |
| OpenAI Endpoint | https://aoai-ai-chat.openai.azure.com/ |
| Cosmos DB Endpoint | https://cosmos-ai-chat.documents.azure.com:443/ |

---

*文档版本：1.0*
*创建时间：2024-12-17*