import logging
import os
import uuid
from typing import List, Optional, Dict, Any, Union

import hvac
import redis
from pydantic import validator, field_validator
from pydantic_settings import BaseSettings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Configure specific loggers
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("fastapi").setLevel(logging.INFO)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

# Get the logger for this module
logger = logging.getLogger(__name__)


class SecretManager:
    """Class to handle secrets management with HashiCorp Vault."""

    def __init__(self, vault_url: str, vault_token: str, mount_point: str = "secret"):
        """Initialize the Vault client if credentials are provided."""
        self.client = None
        if vault_url and vault_token:
            try:
                self.client = hvac.Client(url=vault_url, token=vault_token)
                if not self.client.is_authenticated():
                    logger.warning("Vault client failed to authenticate")
                    self.client = None
                else:
                    logger.info("Vault client authenticated successfully")
                self.mount_point = mount_point
            except Exception as e:
                logger.error(f"Failed to initialize Vault client: {e}")
                self.client = None
        else:
            logger.info("Vault credentials not provided, using environment variables")

    def get_secret(self, path: str, key: str) -> Optional[str]:
        """Get a secret from Vault or return None if not available."""
        if not self.client:
            return None

        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path, mount_point=self.mount_point
            )
            data = response.get("data", {}).get("data", {})
            return data.get(key)
        except Exception as e:
            logger.error(f"Failed to retrieve secret {path}/{key}: {e}")
            return None


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App settings
    APP_NAME: str = "Tool Registry API"
    API_PREFIX: str = "/api/v1"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    TEST_MODE: bool = False
    AUTH_DISABLED: bool = True

    # Instance ID for distributed deployments
    INSTANCE_ID: str = str(uuid.uuid4())

    # Database settings
    DATABASE_URL: str = "postgresql://postgres:password@db:5432/toolregistry"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_RECYCLE: int = 3600

    # Redis settings
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_TTL: int = 3600  # Default TTL in seconds

    # JWT settings
    JWT_SECRET_KEY: str = "insecure_jwt_secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 100

    # Path to postman collection
    POSTMAN_COLLECTION_PATH: str = "./postman/tool_registry_api_collection.json"
    POSTMAN_ENVIRONMENT_PATH: str = "./postman/tool_registry_environment.json"

    # Vault settings
    VAULT_URL: Optional[str] = None
    VAULT_TOKEN: Optional[str] = None
    VAULT_MOUNT_POINT: str = "secret"

    # Instance metrics collection
    METRICS_ENABLED: bool = True
    
    # Security settings
    ENCRYPTION_KEY: str = "insecure_encryption_key"
    ADMIN_API_KEY: str = "admin-api-key"

    @field_validator("DATABASE_URL")
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL and ensure it's properly formatted."""
        if not v:
            raise ValueError("DATABASE_URL must be provided")
        return v

    def get_redis_client(self) -> redis.Redis:
        """Get a Redis client instance."""
        if not hasattr(self, "_redis_client"):
            try:
                self._redis_client = redis.from_url(self.REDIS_URL)
                # Test the connection
                self._redis_client.ping()
                logger.info("Redis connection established successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._redis_client = None
        return self._redis_client

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Initialize secret manager
secret_manager = SecretManager(
    vault_url=settings.VAULT_URL,
    vault_token=settings.VAULT_TOKEN,
    mount_point=settings.VAULT_MOUNT_POINT,
)

# Configure log level based on settings
log_level = logging.INFO if not settings.DEBUG else logging.DEBUG
logging.getLogger().setLevel(log_level)
logger.setLevel(log_level)

logger.info(f"Starting application with version: {settings.APP_VERSION}")
logger.info(f"Authentication disabled: {settings.AUTH_DISABLED}")
logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
logger.info(f"Test mode: {settings.TEST_MODE}")
logger.info(f"Using database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
logger.info(f"Using Redis: {settings.REDIS_URL}") 