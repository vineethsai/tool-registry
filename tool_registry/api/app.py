from fastapi import FastAPI, Depends, HTTPException, status, Request, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import timedelta, datetime
from redis import Redis
import logging
from pydantic import BaseModel
from sqlalchemy.orm import Session
import jwt

from ..core.registry import ToolRegistry
from ..core.auth import AuthService, AgentAuth, JWTToken
from ..core.credentials import Credential, CredentialVendor
from ..core.database import Base, SessionLocal, engine, get_db, Database
from ..core.config import Settings, SecretManager
from ..core.monitoring import Monitoring, monitor_request
from ..core.rate_limit import RateLimiter, rate_limit_middleware
from ..auth import get_current_agent
from ..auth.models import (
    AgentCreate, AgentResponse, TokenResponse,
    SelfRegisterRequest, ApiKeyRequest, ApiKeyResponse
)
from ..models import Tool, Agent, Policy, Credential, AccessLog, ToolMetadata
from ..schemas import (
    ToolCreate, ToolResponse,
    AgentCreate, AgentResponse,
    PolicyCreate, PolicyResponse,
    CredentialCreate, CredentialResponse,
    ToolMetadataCreate, ToolMetadataResponse
)

class ToolCreateRequest(BaseModel):
    """Request model for creating a new tool."""
    name: str
    description: str
    version: str
    tool_metadata: ToolMetadataCreate

app = FastAPI(
    title="GenAI Tool Registry",
    description="An open-source framework for managing GenAI tool access",
    version="0.1.0"
)

settings = Settings()
secret_manager = SecretManager(settings)
monitoring = Monitoring()
redis_client = Redis.from_url(settings.redis_url) if settings.redis_url else None
rate_limiter = RateLimiter(redis_client=redis_client, rate_limit=settings.rate_limit, time_window=settings.rate_limit_window)

# Create database connection
database = Database(settings.database_url)
SessionLocal = database.SessionLocal

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and tables on startup."""
    database.init_db()
    logging.info("Database tables created.")

app.middleware("http")(rate_limit_middleware(rate_limiter))

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize services
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize core services with the database session getter
tool_registry = ToolRegistry(Database(settings.database_url))
auth_service = AuthService(get_db, secret_manager)
credential_vendor = CredentialVendor()

# Import get_current_agent here to avoid circular imports
from ..auth import get_current_agent

@app.post("/token", response_model=TokenResponse)
@monitor_request
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate an agent and get a JWT token."""
    token = await auth_service.authenticate_agent(form_data.username, form_data.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=token, token_type="bearer")

@app.post("/register", response_model=AgentResponse)
@monitor_request
async def self_register(register_data: SelfRegisterRequest):
    """Allow users to register themselves without admin privileges."""
    # Register the new agent
    agent = await auth_service.register_agent(register_data, register_data.password)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )
    
    # Return the agent response
    return AgentResponse(
        id=agent.agent_id,
        name=agent.name,
        roles=agent.roles,
        permissions=agent.permissions,
        created_at=agent.created_at,
        updated_at=agent.created_at
    )

@app.post("/api-keys", response_model=ApiKeyResponse)
@monitor_request
async def create_api_key(key_request: ApiKeyRequest, current_agent: Agent = Depends(get_current_agent)):
    """Create a new API key for programmatic access."""
    api_key = await auth_service.create_api_key(current_agent.agent_id, key_request)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create API key"
        )
    
    return ApiKeyResponse(
        key_id=api_key.key_id,
        api_key=api_key.api_key,
        name=api_key.name,
        expires_at=api_key.expires_at or datetime.utcnow() + timedelta(days=365),
        created_at=api_key.created_at
    )

@app.post("/auth/api-key", response_model=TokenResponse)
@monitor_request
async def authenticate_with_api_key(api_key: str = Header(..., description="API Key for authentication")):
    """Authenticate using an API key and return a JWT token."""
    agent = await auth_service.authenticate_with_api_key(api_key)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create a JWT token for the authenticated agent
    token_data = {
        "sub": str(agent.agent_id),
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    
    access_token = jwt.encode(token_data, auth_service.secret_key, algorithm=auth_service.algorithm)
    return TokenResponse(access_token=access_token, token_type="bearer")

@app.post("/agents", response_model=AgentResponse)
@monitor_request
async def create_agent(agent: AgentCreate, token: str = Depends(oauth2_scheme)):
    """Create a new agent."""
    if not await auth_service.is_admin(token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create agents"
        )
    return await auth_service.create_agent(agent)

@app.post("/tools/", response_model=ToolResponse)
@monitor_request
async def register_tool(tool_request: ToolCreateRequest, token: str = Depends(oauth2_scheme)):
    """Register a new tool."""
    agent = await get_current_agent(token)
    if not auth_service.is_admin(agent):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to register tools"
        )
    # Create a new Tool object from the request
    tool = Tool(
        tool_id=uuid4(),
        name=tool_request.name,
        description=tool_request.description,
        version=tool_request.version,
        tool_metadata_rel=tool_request.tool_metadata,
        endpoint=f"/api/tools/{tool_request.name}",
        auth_required=True
    )
    tool_id = await tool_registry.register_tool(tool)
    # Return the tool that was registered
    return tool

@app.get("/tools", response_model=List[ToolResponse])
@monitor_request
async def list_tools(token: str = Depends(oauth2_scheme)):
    """List all tools."""
    agent = await get_current_agent(token)
    return await tool_registry.list_tools()

@app.get("/tools/search", response_model=List[ToolResponse])
@monitor_request
async def search_tools(query: str, token: str = Depends(oauth2_scheme)):
    """Search tools by name, description, or tags."""
    agent = await get_current_agent(token)
    return await tool_registry.search_tools(query)

@app.get("/tools/{tool_id}", response_model=ToolResponse)
@monitor_request
async def get_tool(tool_id: UUID, token: str = Depends(oauth2_scheme)):
    """Get a tool by ID."""
    agent = await get_current_agent(token)
    tool = await tool_registry.get_tool(tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    return tool

@app.post("/tools/{tool_id}/access", response_model=CredentialResponse)
async def request_tool_access(
    tool_id: UUID,
    duration: Optional[int] = None,
    scopes: Optional[List[str]] = None,
    current_agent: Agent = Depends(get_current_agent)
):
    """Request access to a tool."""
    tool = await tool_registry.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    if not auth_service.check_permission(current_agent, f"access_tool:{tool_id}"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    
    duration_timedelta = timedelta(minutes=duration) if duration else None
    return credential_vendor.generate_credential(
        agent_id=current_agent.agent_id,
        tool_id=tool_id,
        duration=duration_timedelta,
        scopes=scopes
    )

@app.put("/tools/{tool_id}", response_model=ToolResponse)
@monitor_request
async def update_tool(tool_id: UUID, tool_request: ToolCreateRequest, token: str = Depends(oauth2_scheme)):
    """Update a tool."""
    agent = await get_current_agent(token)
    if not auth_service.is_admin(agent):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update tools"
        )
    
    # Get existing tool to preserve other data
    existing_tool = await tool_registry.get_tool(tool_id)
    if not existing_tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    
    # Create updated Tool object with new metadata
    updated_tool = Tool(
        tool_id=tool_id,
        name=tool_request.name,
        description=tool_request.description,
        version=tool_request.version,
        tool_metadata_rel=tool_request.tool_metadata,
        endpoint=f"/api/tools/{tool_request.name}",
        auth_required=True
    )
    await tool_registry.update_tool(updated_tool)
    return updated_tool

@app.delete("/tools/{tool_id}", response_model=bool)
@monitor_request
async def delete_tool(tool_id: UUID, token: str = Depends(oauth2_scheme)):
    """Delete a tool."""
    agent = await get_current_agent(token)
    if not auth_service.is_admin(agent):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete tools"
        )
    success = await tool_registry.delete_tool(tool_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    return success

@app.get("/health")
async def health_check():
    """Check the health of the service."""
    health_status = {
        "status": "healthy",
        "components": {
            "api": "healthy"
        }
    }
    
    # Check database connection
    try:
        session = next(get_db())
        session.execute("SELECT 1")
        health_status["components"]["database"] = "healthy"
    except Exception as e:
        health_status["components"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis connection if configured
    if redis_client:
        try:
            redis_client.ping()
            health_status["components"]["redis"] = "healthy"
        except Exception as e:
            health_status["components"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
    else:
        health_status["components"]["redis"] = "not configured"
    
    return health_status 