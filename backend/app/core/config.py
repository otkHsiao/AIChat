"""Application configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- 🔐 Sensitive Keys (Store in Azure Key Vault in production) ---
    azure_openai_api_key: str
    cosmos_db_key: str
    azure_storage_connection_string: str
    jwt_secret_key: str

    # --- Azure OpenAI Configuration ---
    azure_openai_endpoint: str
    azure_openai_deployment_name: str = "gpt-4o"
    azure_openai_api_version: str = "2024-08-06"

    # --- Cosmos DB Configuration ---
    cosmos_db_endpoint: str
    cosmos_db_database_name: str = "ai-chat-db"

    # --- Blob Storage Configuration ---
    azure_storage_container_name: str = "uploads"

    # --- JWT Configuration ---
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    jwt_refresh_expiration_days: int = 7

    # --- CORS Configuration ---
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # --- Application Configuration ---
    environment: str = "development"
    debug: bool = True

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string to list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()