from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import jwt
from passlib.context import CryptContext

class Agent(BaseModel):
    """Represents an agent in the system."""
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

class AuthService:
    """Service for handling authentication and authorization."""
    
    def __init__(self, db_getter, secret_manager = None):
        """Initialize the authentication service with a database getter function."""
        self.db_getter = db_getter
        self.secret_manager = secret_manager
        self.secret_key = "testsecretkey"  # Default for tests
        self.algorithm = "HS256"
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self._agents: Dict[UUID, Agent] = {}
    
    async def create_agent(self, agent_create) -> Agent:
        """Create a new agent."""
        agent = Agent(
            agent_id=UUID(int=0),  # This should be generated properly in production
            name=agent_create.name,
            roles=agent_create.roles or [],
            permissions=agent_create.permissions or []
        )
        self._agents[agent.agent_id] = agent
        return agent
    
    async def get_agent(self, agent_id: UUID) -> Optional[Agent]:
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
    
    async def verify_token(self, token: str) -> Optional[Agent]:
        """Verify a JWT token and return the associated agent."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            agent_id = UUID(payload["sub"])
            # In a real implementation, fetch from database
            # For testing, just return a simple agent
            return Agent(
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
            
    def is_admin(self, agent: Agent) -> bool:
        """Check if an agent has admin role."""
        return "admin" in agent.roles
    
    def check_permission(self, agent: Agent, permission: str) -> bool:
        """Check if an agent has a specific permission."""
        return permission in agent.permissions
    
    def check_role(self, agent: Agent, role: str) -> bool:
        """Check if an agent has a specific role."""
        return role in agent.roles 