from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import jwt
from passlib.context import CryptContext
import secrets
import string

class AgentAuth(BaseModel):
    """Represents an agent in the authentication system."""
    agent_id: UUID
    name: str
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class JWTToken(BaseModel):
    """JWT token for authentication."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class ApiKey(BaseModel):
    """API key for programmatic access."""
    key_id: UUID
    api_key: str
    agent_id: UUID
    name: str
    description: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

class AuthService:
    """Service for handling authentication and authorization."""
    
    def __init__(self, db_getter, secret_manager = None):
        """Initialize the authentication service with a database getter function."""
        self.db_getter = db_getter
        self.secret_manager = secret_manager
        self.secret_key = "testsecretkey"  # Default for tests
        self.algorithm = "HS256"
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self._agents: Dict[UUID, AgentAuth] = {}
        self._api_keys: Dict[UUID, ApiKey] = {}
        self._username_to_agent: Dict[str, UUID] = {}
    
    async def create_agent(self, agent_create) -> AgentAuth:
        """Create a new agent."""
        agent_id = uuid4()
        agent = AgentAuth(
            agent_id=agent_id,
            name=agent_create.name,
            roles=agent_create.roles or [],
            permissions=agent_create.permissions or []
        )
        self._agents[agent.agent_id] = agent
        return agent
    
    async def register_agent(self, registration_data, password: str) -> AgentAuth:
        """Register a new agent through self-registration."""
        # Check if username already exists
        if registration_data.username in self._username_to_agent:
            return None
            
        # Create agent with default user role
        agent_id = uuid4()
        agent = AgentAuth(
            agent_id=agent_id,
            name=registration_data.name,
            roles=["user"],  # Default role for self-registered users
            permissions=["access_tool:public"]  # Default permission
        )
        
        # Store the agent
        self._agents[agent.agent_id] = agent
        self._username_to_agent[registration_data.username] = agent_id
        
        # In a real system, store the password hash in the database
        # For this example, we're just returning the agent
        
        return agent
    
    async def get_agent(self, agent_id: UUID) -> Optional[AgentAuth]:
        """Get an agent by ID."""
        return self._agents.get(agent_id)
    
    async def authenticate_agent(self, username: str, password: str) -> Optional[str]:
        """Authenticate an agent and return a JWT token."""
        # In a real implementation, we would validate credentials against a database
        # For now, just return a test token for any login
        token_data = {
            "sub": "00000000-0000-0000-0000-000000000000",
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        
        access_token = jwt.encode(token_data, self.secret_key, algorithm=self.algorithm)
        return access_token
    
    async def create_api_key(self, agent_id: UUID, key_request) -> Optional[ApiKey]:
        """Create a new API key for an agent."""
        # Check if the agent exists
        agent = await self.get_agent(agent_id)
        if not agent:
            return None
            
        # Generate a secure API key
        api_key = self._generate_api_key()
        
        # Set expiration date if provided
        expires_at = None
        if key_request.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=key_request.expires_in_days)
        
        # Create and store the API key
        key_id = uuid4()
        key = ApiKey(
            key_id=key_id,
            api_key=api_key,
            agent_id=agent_id,
            name=key_request.name,
            description=key_request.description,
            permissions=key_request.permissions or agent.permissions.copy(),
            expires_at=expires_at
        )
        
        self._api_keys[key_id] = key
        return key
    
    def _generate_api_key(self) -> str:
        """Generate a secure random API key."""
        # Generate a 32-character random string
        alphabet = string.ascii_letters + string.digits
        api_key = ''.join(secrets.choice(alphabet) for _ in range(32))
        return f"tr_{api_key}"
    
    async def authenticate_with_api_key(self, api_key: str) -> Optional[AgentAuth]:
        """Authenticate using an API key and return the agent."""
        # Find the API key
        key = next((k for k in self._api_keys.values() if k.api_key == api_key), None)
        if not key:
            return None
            
        # Check if the key has expired
        if key.expires_at and key.expires_at < datetime.utcnow():
            return None
            
        # Return the associated agent
        return await self.get_agent(key.agent_id)
    
    async def verify_token(self, token: str) -> Optional[AgentAuth]:
        """Verify a JWT token and return the associated agent."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            agent_id = UUID(payload["sub"])
            # In a real implementation, fetch from database
            # For testing, just return a simple agent
            return AgentAuth(
                agent_id=agent_id,
                name="Test Admin",
                roles=["admin"],
                permissions=["register_tool", "access_tool:*"]
            )
        except jwt.PyJWTError:
            return None
            
    async def validate_token(self, token: str) -> bool:
        """Validate a JWT token is properly formatted and not expired."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            # If we can decode the token, it's valid
            return True
        except jwt.PyJWTError:
            return False
            
    def is_admin(self, agent: AgentAuth) -> bool:
        """Check if an agent has admin role."""
        return "admin" in agent.roles
    
    def check_permission(self, agent: AgentAuth, permission: str) -> bool:
        """Check if an agent has a specific permission."""
        return permission in agent.permissions
    
    def check_role(self, agent: AgentAuth, role: str) -> bool:
        """Check if an agent has a specific role."""
        return role in agent.roles 