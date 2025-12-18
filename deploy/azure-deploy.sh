#!/bin/bash
# Azure Deployment Script for AI Chat Application
# This script creates all necessary Azure resources and deploys the application

set -e

# Configuration - Update these variables
RESOURCE_GROUP="rg-ai-chat"
LOCATION="eastasia"
ACR_NAME="acraichat$(openssl rand -hex 4)"  # Unique name
APP_SERVICE_PLAN="asp-ai-chat"
BACKEND_APP_NAME="api-ai-chat-$(openssl rand -hex 4)"
FRONTEND_APP_NAME="web-ai-chat-$(openssl rand -hex 4)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== AI Chat Azure Deployment ===${NC}"

# Check if Azure CLI is logged in
echo -e "${YELLOW}Checking Azure CLI login status...${NC}"
if ! az account show &> /dev/null; then
    echo -e "${RED}Please login to Azure CLI first: az login${NC}"
    exit 1
fi

# Get current subscription
SUBSCRIPTION=$(az account show --query name -o tsv)
echo -e "${GREEN}Using subscription: $SUBSCRIPTION${NC}"

# Create Resource Group if not exists
echo -e "${YELLOW}Creating resource group...${NC}"
az group create --name $RESOURCE_GROUP --location $LOCATION --output none || true
echo -e "${GREEN}Resource group '$RESOURCE_GROUP' ready${NC}"

# Create Azure Container Registry
echo -e "${YELLOW}Creating Azure Container Registry...${NC}"
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --admin-enabled true \
    --output none

ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

echo -e "${GREEN}ACR created: $ACR_LOGIN_SERVER${NC}"

# Build and push Docker images
echo -e "${YELLOW}Building and pushing Docker images...${NC}"

# Login to ACR
az acr login --name $ACR_NAME

# Build backend image
echo -e "${YELLOW}Building backend image...${NC}"
docker build -t $ACR_LOGIN_SERVER/ai-chat-backend:latest ./backend
docker push $ACR_LOGIN_SERVER/ai-chat-backend:latest

# Build frontend image
echo -e "${YELLOW}Building frontend image...${NC}"
docker build -t $ACR_LOGIN_SERVER/ai-chat-frontend:latest ./frontend
docker push $ACR_LOGIN_SERVER/ai-chat-frontend:latest

# Create App Service Plan
echo -e "${YELLOW}Creating App Service Plan...${NC}"
az appservice plan create \
    --name $APP_SERVICE_PLAN \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --is-linux \
    --sku B1 \
    --output none

echo -e "${GREEN}App Service Plan created${NC}"

# Create Backend Web App
echo -e "${YELLOW}Creating Backend Web App...${NC}"
az webapp create \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_SERVICE_PLAN \
    --deployment-container-image-name $ACR_LOGIN_SERVER/ai-chat-backend:latest \
    --output none

# Configure Backend Web App
az webapp config container set \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --docker-registry-server-url https://$ACR_LOGIN_SERVER \
    --docker-registry-server-user $ACR_USERNAME \
    --docker-registry-server-password $ACR_PASSWORD \
    --output none

BACKEND_URL="https://$BACKEND_APP_NAME.azurewebsites.net"
echo -e "${GREEN}Backend Web App created: $BACKEND_URL${NC}"

# Create Frontend Web App
echo -e "${YELLOW}Creating Frontend Web App...${NC}"
az webapp create \
    --name $FRONTEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_SERVICE_PLAN \
    --deployment-container-image-name $ACR_LOGIN_SERVER/ai-chat-frontend:latest \
    --output none

# Configure Frontend Web App
az webapp config container set \
    --name $FRONTEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --docker-registry-server-url https://$ACR_LOGIN_SERVER \
    --docker-registry-server-user $ACR_USERNAME \
    --docker-registry-server-password $ACR_PASSWORD \
    --output none

# Set Frontend environment variable for API URL
az webapp config appsettings set \
    --name $FRONTEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings API_URL=$BACKEND_URL \
    --output none

FRONTEND_URL="https://$FRONTEND_APP_NAME.azurewebsites.net"
echo -e "${GREEN}Frontend Web App created: $FRONTEND_URL${NC}"

# Output summary
echo ""
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "Container Registry: $ACR_LOGIN_SERVER"
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""
echo -e "${YELLOW}IMPORTANT: Configure Backend Environment Variables${NC}"
echo "Run the following command to set backend environment variables:"
echo ""
echo "az webapp config appsettings set \\"
echo "    --name $BACKEND_APP_NAME \\"
echo "    --resource-group $RESOURCE_GROUP \\"
echo "    --settings \\"
echo "    AZURE_OPENAI_ENDPOINT=\"<your-openai-endpoint>\" \\"
echo "    AZURE_OPENAI_API_KEY=\"<your-openai-key>\" \\"
echo "    AZURE_OPENAI_DEPLOYMENT_NAME=\"gpt-4o\" \\"
echo "    COSMOS_DB_ENDPOINT=\"<your-cosmos-endpoint>\" \\"
echo "    COSMOS_DB_KEY=\"<your-cosmos-key>\" \\"
echo "    AZURE_STORAGE_CONNECTION_STRING=\"<your-storage-connection>\" \\"
echo "    JWT_SECRET_KEY=\"<your-jwt-secret>\" \\"
echo "    CORS_ORIGINS=\"$FRONTEND_URL\""
echo ""
echo -e "${GREEN}Don't forget to update CORS_ORIGINS in backend settings!${NC}"