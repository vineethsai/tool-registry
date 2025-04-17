import logging
import logging.config
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from hvac import Client as VaultClient
from dotenv import load_dotenv
import secrets

load_dotenv()

# Define logging configuration dictionary
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "DEBUG",  # Capture debug level and above
        },
    },
    "loggers": {
        "tool_registry": {  # Root logger for the application
            "handlers": ["console"],
            "level": "INFO",  # Default level for the app
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": { # Catch-all root logger
        "handlers": ["console"],
        "level": "WARNING", # Log warnings and above from other libraries
    },
}

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./tool_registry.db")
    )
    
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
    
    # CORS Settings
    # Comma-separated list of allowed origins
    cors_allowed_origins: str = Field(
        default="http://localhost,http://localhost:3000,http://localhost:8000,http://localhost:8080",
        description="Comma-separated list of allowed origins for CORS"
    )
    # Whether to allow credentials
    cors_allow_credentials: bool = True
    # Comma-separated list of allowed methods
    cors_allowed_methods: str = "GET,POST,PUT,DELETE,OPTIONS"
    # Comma-separated list of allowed headers
    cors_allowed_headers: str = "*"
    
    # Logging level - will be used to set the app logger level
    log_level: str = Field(default="INFO")
    
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

# Configure logging
LOGGING_CONFIG["loggers"]["tool_registry"]["level"] = settings.log_level.upper()
logging.config.dictConfig(LOGGING_CONFIG)

# Initialize secret manager
secret_manager = SecretManager(settings)

# Get a logger instance for this module (optional, for testing config)
logger = logging.getLogger(__name__)
logger.info(f"Logging configured with level: {settings.log_level.upper()}") 