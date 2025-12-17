# 环境变量配置指南

## 环境变量分类

环境变量分为三类：

| 类型 | 存储位置 | 说明 |
|------|----------|------|
| 🔐 **敏感密钥** | Azure Key Vault | API Keys、数据库密钥、JWT Secret 等 |
| ⚙️ **配置项** | App Service 设置 | 端点 URL、数据库名称等非敏感配置 |
| 🛠️ **本地开发** | `.env.local` | 仅用于本地开发，不提交到 Git |

---

## 后端环境变量详细说明

### 🔐 必须存入 Key Vault 的密钥

| 变量名 | Key Vault Secret 名称 | 说明 |
|--------|----------------------|------|
| `AZURE_OPENAI_API_KEY` | `azure-openai-api-key` | Azure OpenAI 服务密钥 |
| `COSMOS_DB_KEY` | `cosmos-db-key` | Cosmos DB 主密钥 |
| `AZURE_STORAGE_CONNECTION_STRING` | `storage-connection-string` | Blob Storage 连接字符串 |
| `JWT_SECRET_KEY` | `jwt-secret-key` | JWT 签名密钥 (至少 32 字符) |

### ⚙️ App Service 配置项 (非敏感)

| 变量名 | 示例值 | 说明 |
|--------|--------|------|
| `AZURE_OPENAI_ENDPOINT` | `https://aoai-ai-chat.openai.azure.com/` | OpenAI 端点 URL |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | `gpt-4o` | 模型部署名称 |
| `AZURE_OPENAI_API_VERSION` | `2024-08-06` | API 版本 |
| `COSMOS_DB_ENDPOINT` | `https://cosmos-ai-chat.documents.azure.com:443/` | Cosmos DB 端点 |
| `COSMOS_DB_DATABASE_NAME` | `ai-chat-db` | 数据库名称 |
| `AZURE_STORAGE_CONTAINER_NAME` | `uploads` | Blob 容器名称 |
| `JWT_ALGORITHM` | `HS256` | JWT 算法 |
| `JWT_EXPIRATION_HOURS` | `24` | Token 过期时间 |
| `CORS_ORIGINS` | `https://app-ai-chat-fe.azurewebsites.net` | 允许的前端域名 |
| `ENVIRONMENT` | `production` | 运行环境 |

---

## 前端环境变量

前端只需要一个环境变量（构建时注入）：

| 变量名 | 位置 | 说明 |
|--------|------|------|
| `VITE_API_BASE_URL` | App Service 设置 | 后端 API 地址 |

---

## 本地开发配置

### 文件：`backend/.env.local`

```env
# ============================================
# 🛠️ 本地开发环境配置
# ⚠️ 此文件不要提交到 Git！
# ============================================

# --- 🔐 敏感密钥 (生产环境存入 Key Vault) ---
AZURE_OPENAI_API_KEY=your-openai-api-key-here
COSMOS_DB_KEY=your-cosmos-db-key-here
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=xxx;AccountKey=xxx;EndpointSuffix=core.windows.net
JWT_SECRET_KEY=your-super-secret-jwt-key-at-least-32-chars

# --- ⚙️ 配置项 ---
AZURE_OPENAI_ENDPOINT=https://aoai-ai-chat.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-06

COSMOS_DB_ENDPOINT=https://cosmos-ai-chat.documents.azure.com:443/
COSMOS_DB_DATABASE_NAME=ai-chat-db

AZURE_STORAGE_CONTAINER_NAME=uploads

JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# --- 环境标识 ---
ENVIRONMENT=development
```

### 文件：`frontend/.env.local`

```env
# 本地开发后端地址
VITE_API_BASE_URL=http://localhost:8000/api
```

---

## 生产环境配置

### Azure App Service 配置

后端 Web App 需要配置以下设置：

```bash
# 1. 非敏感配置项 (直接设置)
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
    JWT_ALGORITHM="HS256" \
    JWT_EXPIRATION_HOURS="24" \
    CORS_ORIGINS="https://app-ai-chat-fe.azurewebsites.net" \
    ENVIRONMENT="production"

# 2. 敏感密钥 (Key Vault 引用)
az webapp config appsettings set \
  --name app-ai-chat-be \
  --resource-group rg-ai-chat \
  --settings \
    AZURE_OPENAI_API_KEY="@Microsoft.KeyVault(VaultName=kv-ai-chat;SecretName=azure-openai-api-key)" \
    COSMOS_DB_KEY="@Microsoft.KeyVault(VaultName=kv-ai-chat;SecretName=cosmos-db-key)" \
    AZURE_STORAGE_CONNECTION_STRING="@Microsoft.KeyVault(VaultName=kv-ai-chat;SecretName=storage-connection-string)" \
    JWT_SECRET_KEY="@Microsoft.KeyVault(VaultName=kv-ai-chat;SecretName=jwt-secret-key)"
```

### Key Vault 密钥创建

```bash
# 1. 获取并存储 OpenAI API Key
OPENAI_KEY=$(az cognitiveservices account keys list \
  --name aoai-ai-chat \
  --resource-group rg-ai-chat \
  --query key1 -o tsv)

az keyvault secret set \
  --vault-name kv-ai-chat \
  --name azure-openai-api-key \
  --value "$OPENAI_KEY"

# 2. 获取并存储 Cosmos DB Key
COSMOS_KEY=$(az cosmosdb keys list \
  --name cosmos-ai-chat \
  --resource-group rg-ai-chat \
  --query primaryMasterKey -o tsv)

az keyvault secret set \
  --vault-name kv-ai-chat \
  --name cosmos-db-key \
  --value "$COSMOS_KEY"

# 3. 获取并存储 Storage 连接字符串
STORAGE_CONN=$(az storage account show-connection-string \
  --name stgaichat \
  --resource-group rg-ai-chat \
  --query connectionString -o tsv)

az keyvault secret set \
  --vault-name kv-ai-chat \
  --name storage-connection-string \
  --value "$STORAGE_CONN"

# 4. 生成并存储 JWT Secret (随机 64 字符)
JWT_SECRET=$(openssl rand -base64 48)

az keyvault secret set \
  --vault-name kv-ai-chat \
  --name jwt-secret-key \
  --value "$JWT_SECRET"
```

---

## 文件清单

```
ai-chat/
├── .gitignore                    # 包含 .env.local
├── .env.example                  # 环境变量模板 (提交到 Git)
├── backend/
│   ├── .env.local               # 🚫 不提交 - 本地开发密钥
│   └── .env.example             # ✅ 提交 - 模板文件
└── frontend/
    ├── .env.local               # 🚫 不提交 - 本地开发配置
    └── .env.example             # ✅ 提交 - 模板文件
```

---

## .gitignore 配置

确保以下内容在 `.gitignore` 中：

```gitignore
# 环境变量文件
.env
.env.local
.env.*.local
*.local.env

# 不忽略示例文件
!.env.example
```

---

## 后端代码中读取环境变量

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # 🔐 敏感密钥 (来自 Key Vault 或 .env.local)
    azure_openai_api_key: str
    cosmos_db_key: str
    azure_storage_connection_string: str
    jwt_secret_key: str
    
    # ⚙️ 配置项
    azure_openai_endpoint: str
    azure_openai_deployment_name: str = "gpt-4o"
    azure_openai_api_version: str = "2024-08-06"
    
    cosmos_db_endpoint: str
    cosmos_db_database_name: str = "ai-chat-db"
    
    azure_storage_container_name: str = "uploads"
    
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    cors_origins: str = "http://localhost:3000"
    environment: str = "development"
    
    class Config:
        env_file = ".env.local"
        env_file_encoding = "utf-8"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

## 安全检查清单

- [ ] `.env.local` 已添加到 `.gitignore`
- [ ] 敏感密钥仅存储在 Key Vault
- [ ] App Service 已启用 Managed Identity
- [ ] Key Vault 访问策略已配置
- [ ] 生产环境不使用默认密钥
- [ ] JWT Secret 至少 32 字符

---

*文档版本：1.0*
*创建时间：2024-12-17*