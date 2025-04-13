from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from .models import Agent, Tool, Credential

class CredentialVendor:
    """Service for generating and managing temporary credentials."""
    
    def __init__(self):
        self.credentials = {}  # In-memory storage, replace with database in production
    
    async def generate_credential(
        self,
        agent: Agent,
        tool: Tool,
        duration: Optional[timedelta] = None
    ) -> Credential:
        """
        Generate a temporary credential for tool access.
        
        Args:
            agent: The agent requesting the credential
            tool: The tool the credential should grant access to
            duration: How long the credential should be valid for
            
        Returns:
            Credential: The generated temporary credential
        """
        if duration is None:
            duration = timedelta(minutes=15)  # Default duration
        
        # Generate a temporary token
        token = self._generate_token(agent, tool)
        
        # Create credential
        credential = Credential(
            agent_id=agent.agent_id,
            tool_id=tool.tool_id,
            token=token,
            expires_at=datetime.utcnow() + duration
        )
        
        # Store credential
        self.credentials[credential.credential_id] = credential
        
        return credential
    
    def _generate_token(self, agent: Agent, tool: Tool) -> str:
        """
        Generate a secure token for tool access.
        
        Args:
            agent: The agent requesting access
            tool: The tool being accessed
            
        Returns:
            str: A secure token
        """
        # TODO: Implement secure token generation
        # This is a placeholder implementation
        return f"temp_token_{agent.agent_id}_{tool.tool_id}"
    
    async def validate_credential(self, token: str) -> Optional[Credential]:
        """
        Validate a credential token.
        
        Args:
            token: The token to validate
            
        Returns:
            Optional[Credential]: The credential if valid, None otherwise
        """
        # Find credential by token
        credential = next(
            (c for c in self.credentials.values() if c.token == token),
            None
        )
        
        if not credential:
            return None
        
        # Check if expired
        if datetime.utcnow() > credential.expires_at:
            return None
        
        return credential
    
    def revoke_credential(self, credential_id: UUID) -> None:
        """
        Revoke a credential.
        
        Args:
            credential_id: The ID of the credential to revoke
        """
        if credential_id in self.credentials:
            del self.credentials[credential_id]
    
    def cleanup_expired_credentials(self) -> None:
        """Remove all expired credentials."""
        now = datetime.utcnow()
        expired_ids = [
            credential_id
            for credential_id, credential in self.credentials.items()
            if credential.expires_at < now
        ]
        for credential_id in expired_ids:
            del self.credentials[credential_id] 