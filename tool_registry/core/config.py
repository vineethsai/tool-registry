import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from hvac import Client as VaultClient
from dotenv import load_dotenv
import secrets

load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "sqlite:///./tool_registry.db"
    
    # HashiCorp Vault settings
    vault_url: Optional[str] = None
    vault_token: Optional[str] = None
    vault_mount_point: str = "secret"
    
    # JWT settings
    jwt_secret_key: str = Field(default_factory=lambda: secrets.token_hex(32))
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    
    # Rate limiting
    redis_url: Optional[str] = "redis://localhost:6379/0"
    rate_limit: int = 100  # requests per time window
    rate_limit_window: int = 60  # time window in seconds
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

class SecretManager:
    def __init__(self, settings: Settings):
        self.vault_client = VaultClient(
            url=settings.vault_url,
            token=settings.vault_token
        )
        self.vault_path = settings.vault_mount_point
    
    def get_secret(self, path: str) -> dict:
        """Get a secret from Vault."""
        try:
            response = self.vault_client.secrets.kv.v2.read_secret_version(
                path=f"{self.vault_path}/{path}"
            )
            return response["data"]["data"]
        except Exception as e:
            print(f"Error retrieving secret: {e}")
            return {}
    
    def set_secret(self, path: str, data: dict) -> bool:
        """Set a secret in Vault."""
        try:
            self.vault_client.secrets.kv.v2.create_or_update_secret(
                path=f"{self.vault_path}/{path}",
                secret=data
            )
            return True
        except Exception as e:
            print(f"Error setting secret: {e}")
            return False

# Initialize settings
settings = Settings()

# Initialize secret manager
secret_manager = SecretManager(settings) 