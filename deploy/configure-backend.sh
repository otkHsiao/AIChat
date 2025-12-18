#!/bin/bash
# Configure Backend Environment Variables
# Run this script after creating the App Service

set -e

# Configuration - Update these with your values
RESOURCE_GROUP="rg-ai-chat"
BACKEND_APP_NAME="your-backend-app-name"

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT="https://aoai-ai-chat-xc.openai.azure.com/"
AZURE_OPENAI_API_KEY="your-api-key"
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"
AZURE_OPENAI_API_VERSION="2024-02-15-preview"

# Cosmos DB Configuration
COSMOS_DB_ENDPOINT="https://cosmosaichatxc.documents.azure.com:443/"
COSMOS_DB_KEY="your-cosmos-key"
COSMOS_DB_DATABASE_NAME="chatdb"

# Blob Storage Configuration
AZURE_STORAGE_CONNECTION_STRING="your-storage-connection-string"
AZURE_STORAGE_CONTAINER_NAME="uploads"

# JWT Configuration
JWT_SECRET_KEY="your-secure-jwt-secret-key-here"
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES="30"
JWT_REFRESH_TOKEN_EXPIRE_DAYS="7"

# CORS Configuration
CORS_ORIGINS="https://your-frontend-url.azurewebsites.net"

# Apply settings
echo "Configuring backend environment variables..."
az webapp config appsettings set \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
    AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
    AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
    AZURE_OPENAI_DEPLOYMENT_NAME="$AZURE_OPENAI_DEPLOYMENT_NAME" \
    AZURE_OPENAI_API_VERSION="$AZURE_OPENAI_API_VERSION" \
    COSMOS_DB_ENDPOINT="$COSMOS_DB_ENDPOINT" \
    COSMOS_DB_KEY="$COSMOS_DB_KEY" \
    COSMOS_DB_DATABASE_NAME="$COSMOS_DB_DATABASE_NAME" \
    AZURE_STORAGE_CONNECTION_STRING="$AZURE_STORAGE_CONNECTION_STRING" \
    AZURE_STORAGE_CONTAINER_NAME="$AZURE_STORAGE_CONTAINER_NAME" \
    JWT_SECRET_KEY="$JWT_SECRET_KEY" \
    JWT_ALGORITHM="$JWT_ALGORITHM" \
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES="$JWT_ACCESS_TOKEN_EXPIRE_MINUTES" \
    JWT_REFRESH_TOKEN_EXPIRE_DAYS="$JWT_REFRESH_TOKEN_EXPIRE_DAYS" \
    CORS_ORIGINS="$CORS_ORIGINS"

echo "Backend configuration complete!"