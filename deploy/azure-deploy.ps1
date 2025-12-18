# Azure Deployment Script for AI Chat Application (PowerShell)
# This script creates all necessary Azure resources and deploys the application

$ErrorActionPreference = "Stop"

# Configuration - Update these variables
$RESOURCE_GROUP = "rg-ai-chat"
$LOCATION = "eastasia"
$ACR_NAME = "acraichat$(Get-Random -Minimum 1000 -Maximum 9999)"
$APP_SERVICE_PLAN = "asp-ai-chat"
$BACKEND_APP_NAME = "api-ai-chat-$(Get-Random -Minimum 1000 -Maximum 9999)"
$FRONTEND_APP_NAME = "web-ai-chat-$(Get-Random -Minimum 1000 -Maximum 9999)"

Write-Host "=== AI Chat Azure Deployment ===" -ForegroundColor Green

# Check if Azure CLI is logged in
Write-Host "Checking Azure CLI login status..." -ForegroundColor Yellow
try {
    $account = az account show | ConvertFrom-Json
    Write-Host "Using subscription: $($account.name)" -ForegroundColor Green
} catch {
    Write-Host "Please login to Azure CLI first: az login" -ForegroundColor Red
    exit 1
}

# Create Resource Group if not exists
Write-Host "Creating resource group..." -ForegroundColor Yellow
az group create --name $RESOURCE_GROUP --location $LOCATION --output none 2>$null
Write-Host "Resource group '$RESOURCE_GROUP' ready" -ForegroundColor Green

# Create Azure Container Registry
Write-Host "Creating Azure Container Registry..." -ForegroundColor Yellow
az acr create `
    --resource-group $RESOURCE_GROUP `
    --name $ACR_NAME `
    --sku Basic `
    --admin-enabled true `
    --output none

$ACR_LOGIN_SERVER = az acr show --name $ACR_NAME --query loginServer -o tsv
$ACR_USERNAME = az acr credential show --name $ACR_NAME --query username -o tsv
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv

Write-Host "ACR created: $ACR_LOGIN_SERVER" -ForegroundColor Green

# Build and push Docker images
Write-Host "Building and pushing Docker images..." -ForegroundColor Yellow

# Login to ACR
az acr login --name $ACR_NAME

# Build backend image
Write-Host "Building backend image..." -ForegroundColor Yellow
docker build -t "$ACR_LOGIN_SERVER/ai-chat-backend:latest" ./backend
docker push "$ACR_LOGIN_SERVER/ai-chat-backend:latest"

# Build frontend image
Write-Host "Building frontend image..." -ForegroundColor Yellow
docker build -t "$ACR_LOGIN_SERVER/ai-chat-frontend:latest" ./frontend
docker push "$ACR_LOGIN_SERVER/ai-chat-frontend:latest"

# Create App Service Plan
Write-Host "Creating App Service Plan..." -ForegroundColor Yellow
az appservice plan create `
    --name $APP_SERVICE_PLAN `
    --resource-group $RESOURCE_GROUP `
    --location $LOCATION `
    --is-linux `
    --sku B1 `
    --output none

Write-Host "App Service Plan created" -ForegroundColor Green

# Create Backend Web App
Write-Host "Creating Backend Web App..." -ForegroundColor Yellow
az webapp create `
    --name $BACKEND_APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --plan $APP_SERVICE_PLAN `
    --deployment-container-image-name "$ACR_LOGIN_SERVER/ai-chat-backend:latest" `
    --output none

# Configure Backend Web App
az webapp config container set `
    --name $BACKEND_APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --docker-registry-server-url "https://$ACR_LOGIN_SERVER" `
    --docker-registry-server-user $ACR_USERNAME `
    --docker-registry-server-password $ACR_PASSWORD `
    --output none

$BACKEND_URL = "https://$BACKEND_APP_NAME.azurewebsites.net"
Write-Host "Backend Web App created: $BACKEND_URL" -ForegroundColor Green

# Create Frontend Web App
Write-Host "Creating Frontend Web App..." -ForegroundColor Yellow
az webapp create `
    --name $FRONTEND_APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --plan $APP_SERVICE_PLAN `
    --deployment-container-image-name "$ACR_LOGIN_SERVER/ai-chat-frontend:latest" `
    --output none

# Configure Frontend Web App
az webapp config container set `
    --name $FRONTEND_APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --docker-registry-server-url "https://$ACR_LOGIN_SERVER" `
    --docker-registry-server-user $ACR_USERNAME `
    --docker-registry-server-password $ACR_PASSWORD `
    --output none

# Set Frontend environment variable for API URL
az webapp config appsettings set `
    --name $FRONTEND_APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --settings API_URL=$BACKEND_URL `
    --output none

$FRONTEND_URL = "https://$FRONTEND_APP_NAME.azurewebsites.net"
Write-Host "Frontend Web App created: $FRONTEND_URL" -ForegroundColor Green

# Output summary
Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Resource Group: $RESOURCE_GROUP"
Write-Host "Container Registry: $ACR_LOGIN_SERVER"
Write-Host "Backend URL: $BACKEND_URL"
Write-Host "Frontend URL: $FRONTEND_URL"
Write-Host ""
Write-Host "IMPORTANT: Configure Backend Environment Variables" -ForegroundColor Yellow
Write-Host "Run the following command to set backend environment variables:" -ForegroundColor Yellow
Write-Host ""
Write-Host @"
az webapp config appsettings set ``
    --name $BACKEND_APP_NAME ``
    --resource-group $RESOURCE_GROUP ``
    --settings ``
    AZURE_OPENAI_ENDPOINT="<your-openai-endpoint>" ``
    AZURE_OPENAI_API_KEY="<your-openai-key>" ``
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o" ``
    COSMOS_DB_ENDPOINT="<your-cosmos-endpoint>" ``
    COSMOS_DB_KEY="<your-cosmos-key>" ``
    AZURE_STORAGE_CONNECTION_STRING="<your-storage-connection>" ``
    JWT_SECRET_KEY="<your-jwt-secret>" ``
    CORS_ORIGINS="$FRONTEND_URL"
"@
Write-Host ""
Write-Host "Don't forget to update CORS_ORIGINS in backend settings!" -ForegroundColor Green

# Save deployment info
$deploymentInfo = @{
    ResourceGroup = $RESOURCE_GROUP
    ACRName = $ACR_NAME
    ACRLoginServer = $ACR_LOGIN_SERVER
    BackendAppName = $BACKEND_APP_NAME
    BackendURL = $BACKEND_URL
    FrontendAppName = $FRONTEND_APP_NAME
    FrontendURL = $FRONTEND_URL
}
$deploymentInfo | ConvertTo-Json | Out-File -FilePath "deployment-info.json"
Write-Host "Deployment info saved to deployment-info.json" -ForegroundColor Green