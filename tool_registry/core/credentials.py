from typing import Optional, Dict
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

# Initialize logger for this module
logger = logging.getLogger(__name__)

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
        logger.info("CredentialVendor initialized")
    
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
        
        logger.debug(f"Generating credential for agent ID: {agent_id}, tool ID: {tool_id}")
        logger.debug(f"Duration: {duration}, Scopes: {scopes or []}")
        
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
        
        logger.info(f"Generated credential ID: {credential.credential_id} expiring at {credential.expires_at}")
        return credential
    
    def _generate_token(self, agent_id: UUID, tool_id: UUID) -> str:
        """Generate a unique token for the credential."""
        # In production, use a secure token generation method
        token = f"temp_token_{agent_id}_{tool_id}_{uuid4()}"
        logger.debug(f"Generated token for agent {agent_id} and tool {tool_id}")
        return token
    
    def validate_credential(self, token: str) -> Optional[Credential]:
        """Validate a credential token."""
        logger.debug("Validating credential token")
        
        credential_id = self._token_to_credential.get(token)
        if not credential_id:
            logger.warning("Token not found in credential store")
            return None
        
        credential = self._credentials.get(credential_id)
        if not credential:
            logger.warning(f"Credential ID {credential_id} not found for token")
            return None
        
        if datetime.utcnow() > credential.expires_at:
            logger.warning(f"Credential {credential_id} has expired at {credential.expires_at}")
            self.revoke_credential(credential.credential_id)
            return None
        
        logger.info(f"Successfully validated credential {credential_id} for agent {credential.agent_id}")
        return credential
    
    def revoke_credential(self, credential_id: UUID) -> bool:
        """Revoke a credential."""
        logger.debug(f"Attempting to revoke credential: {credential_id}")
        
        credential = self._credentials.get(credential_id)
        if not credential:
            logger.warning(f"Credential not found for ID: {credential_id}")
            return False
        
        del self._token_to_credential[credential.token]
        del self._credentials[credential_id]
        logger.info(f"Successfully revoked credential: {credential_id}")
        return True
    
    def cleanup_expired_credentials(self) -> None:
        """Remove all expired credentials."""
        logger.debug("Starting cleanup of expired credentials")
        now = datetime.utcnow()
        expired_ids = [
            credential_id
            for credential_id, credential in self._credentials.items()
            if credential.expires_at < now
        ]
        
        for credential_id in expired_ids:
            self.revoke_credential(credential_id)
        
        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired credentials")
        else:
            logger.debug("No expired credentials found during cleanup")
    
    def get_agent_credentials(self, agent_id: UUID) -> list[Credential]:
        """Get all active credentials for an agent."""
        logger.debug(f"Retrieving active credentials for agent: {agent_id}")
        
        credentials = [
            credential
            for credential in self._credentials.values()
            if credential.agent_id == agent_id and credential.expires_at > datetime.utcnow()
        ]
        
        logger.info(f"Found {len(credentials)} active credentials for agent: {agent_id}")
        return credentials 