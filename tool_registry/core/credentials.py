from typing import Optional, Dict
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

class Credential(BaseModel):
    """Represents a temporary credential for tool access."""
    credential_id: UUID = Field(default_factory=uuid4)
    agent_id: UUID
    tool_id: UUID
    token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    scopes: list[str] = Field(default_factory=list)

class CredentialVendor:
    """Service for managing temporary credentials."""
    
    def __init__(self):
        self._credentials: Dict[UUID, Credential] = {}
        self._token_to_credential: Dict[str, UUID] = {}
    
    def generate_credential(
        self,
        agent_id: UUID,
        tool_id: UUID,
        duration: Optional[timedelta] = None,
        scopes: Optional[list[str]] = None
    ) -> Credential:
        """Generate a new temporary credential."""
        if duration is None:
            duration = timedelta(minutes=15)
        
        token = self._generate_token(agent_id, tool_id)
        credential = Credential(
            agent_id=agent_id,
            tool_id=tool_id,
            token=token,
            expires_at=datetime.utcnow() + duration,
            scopes=scopes or []
        )
        
        self._credentials[credential.credential_id] = credential
        self._token_to_credential[token] = credential.credential_id
        
        return credential
    
    def _generate_token(self, agent_id: UUID, tool_id: UUID) -> str:
        """Generate a unique token for the credential."""
        # In production, use a secure token generation method
        return f"temp_token_{agent_id}_{tool_id}_{uuid4()}"
    
    def validate_credential(self, token: str) -> Optional[Credential]:
        """Validate a credential token."""
        credential_id = self._token_to_credential.get(token)
        if not credential_id:
            return None
        
        credential = self._credentials.get(credential_id)
        if not credential:
            return None
        
        if datetime.utcnow() > credential.expires_at:
            self.revoke_credential(credential.credential_id)
            return None
        
        return credential
    
    def revoke_credential(self, credential_id: UUID) -> bool:
        """Revoke a credential."""
        credential = self._credentials.get(credential_id)
        if not credential:
            return False
        
        del self._token_to_credential[credential.token]
        del self._credentials[credential_id]
        return True
    
    def cleanup_expired_credentials(self) -> None:
        """Remove all expired credentials."""
        now = datetime.utcnow()
        expired_ids = [
            credential_id
            for credential_id, credential in self._credentials.items()
            if credential.expires_at < now
        ]
        for credential_id in expired_ids:
            self.revoke_credential(credential_id)
    
    def get_agent_credentials(self, agent_id: UUID) -> list[Credential]:
        """Get all active credentials for an agent."""
        return [
            credential
            for credential in self._credentials.values()
            if credential.agent_id == agent_id and credential.expires_at > datetime.utcnow()
        ] 