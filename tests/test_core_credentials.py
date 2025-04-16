import pytest
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import time

from tool_registry.core.credentials import Credential, CredentialVendor

class TestCredentials:
    """Test suite for the Credentials module."""
    
    def test_credential_model_creation(self):
        """Test that a credential model can be created with all required fields."""
        agent_id = uuid4()
        tool_id = uuid4()
        token = "test_token"
        expires_at = datetime.utcnow() + timedelta(minutes=15)
        
        credential = Credential(
            agent_id=agent_id,
            tool_id=tool_id,
            token=token,
            expires_at=expires_at
        )
        
        assert isinstance(credential.credential_id, UUID)
        assert credential.agent_id == agent_id
        assert credential.tool_id == tool_id
        assert credential.token == token
        assert credential.expires_at == expires_at
        assert isinstance(credential.created_at, datetime)
        assert isinstance(credential.scopes, list)
        assert len(credential.scopes) == 0
    
    def test_credential_vendor_initialization(self):
        """Test that the credential vendor initializes correctly."""
        vendor = CredentialVendor()
        assert vendor._credentials == {}
        assert vendor._token_to_credential == {}
    
    def test_generate_credential(self):
        """Test that a credential can be generated."""
        vendor = CredentialVendor()
        agent_id = uuid4()
        tool_id = uuid4()
        
        credential = vendor.generate_credential(agent_id, tool_id)
        
        assert credential.agent_id == agent_id
        assert credential.tool_id == tool_id
        assert isinstance(credential.token, str)
        assert credential.expires_at > datetime.utcnow()
        assert credential.credential_id in vendor._credentials
        assert credential.token in vendor._token_to_credential
        assert vendor._token_to_credential[credential.token] == credential.credential_id
    
    def test_generate_credential_with_custom_duration(self):
        """Test that a credential can be generated with a custom duration."""
        vendor = CredentialVendor()
        agent_id = uuid4()
        tool_id = uuid4()
        duration = timedelta(hours=1)
        
        credential = vendor.generate_credential(agent_id, tool_id, duration=duration)
        
        # Check if expiration is approximately 1 hour in the future (with some margin for test execution time)
        time_diff = (credential.expires_at - datetime.utcnow()).total_seconds()
        assert 3590 <= time_diff <= 3610  # 1 hour +/- 10 seconds
    
    def test_generate_credential_with_scopes(self):
        """Test that a credential can be generated with specific scopes."""
        vendor = CredentialVendor()
        agent_id = uuid4()
        tool_id = uuid4()
        scopes = ["read", "write"]
        
        credential = vendor.generate_credential(agent_id, tool_id, scopes=scopes)
        
        assert credential.scopes == scopes
    
    def test_validate_credential_valid(self):
        """Test that a valid credential can be validated."""
        vendor = CredentialVendor()
        agent_id = uuid4()
        tool_id = uuid4()
        
        credential = vendor.generate_credential(agent_id, tool_id)
        validated = vendor.validate_credential(credential.token)
        
        assert validated is not None
        assert validated.credential_id == credential.credential_id
    
    def test_validate_credential_invalid_token(self):
        """Test that an invalid token fails validation."""
        vendor = CredentialVendor()
        
        validated = vendor.validate_credential("invalid_token")
        
        assert validated is None
    
    def test_validate_credential_expired(self):
        """Test that an expired credential fails validation."""
        vendor = CredentialVendor()
        agent_id = uuid4()
        tool_id = uuid4()
        
        # Generate a credential that expires immediately
        credential = vendor.generate_credential(
            agent_id, 
            tool_id,
            duration=timedelta(milliseconds=1)
        )
        
        # Wait for it to expire
        time.sleep(0.01)
        
        validated = vendor.validate_credential(credential.token)
        
        assert validated is None
        # The credential should have been revoked
        assert credential.credential_id not in vendor._credentials
    
    def test_revoke_credential(self):
        """Test that a credential can be revoked."""
        vendor = CredentialVendor()
        agent_id = uuid4()
        tool_id = uuid4()
        
        credential = vendor.generate_credential(agent_id, tool_id)
        
        # Verify it exists
        assert credential.credential_id in vendor._credentials
        assert credential.token in vendor._token_to_credential
        
        # Revoke it
        result = vendor.revoke_credential(credential.credential_id)
        
        assert result is True
        assert credential.credential_id not in vendor._credentials
        assert credential.token not in vendor._token_to_credential
    
    def test_revoke_nonexistent_credential(self):
        """Test that revoking a nonexistent credential returns False."""
        vendor = CredentialVendor()
        
        result = vendor.revoke_credential(uuid4())
        
        assert result is False
    
    def test_cleanup_expired_credentials(self):
        """Test that expired credentials are cleaned up."""
        vendor = CredentialVendor()
        agent_id = uuid4()
        tool_id = uuid4()
        
        # Generate one credential that expires immediately
        credential1 = vendor.generate_credential(
            agent_id, 
            tool_id,
            duration=timedelta(milliseconds=1)
        )
        
        # Generate one credential that's valid for longer
        credential2 = vendor.generate_credential(
            agent_id, 
            tool_id,
            duration=timedelta(minutes=10)
        )
        
        # Wait for the first one to expire
        time.sleep(0.01)
        
        # Clean up expired credentials
        vendor.cleanup_expired_credentials()
        
        # Check that only credential1 was removed
        assert credential1.credential_id not in vendor._credentials
        assert credential1.token not in vendor._token_to_credential
        assert credential2.credential_id in vendor._credentials
        assert credential2.token in vendor._token_to_credential
    
    def test_get_agent_credentials(self):
        """Test getting all credentials for a specific agent."""
        vendor = CredentialVendor()
        agent1_id = uuid4()
        agent2_id = uuid4()
        tool_id = uuid4()
        
        # Generate two credentials for agent1
        credential1 = vendor.generate_credential(agent1_id, tool_id)
        credential2 = vendor.generate_credential(agent1_id, tool_id)
        
        # Generate one credential for agent2
        credential3 = vendor.generate_credential(agent2_id, tool_id)
        
        # Get credentials for agent1
        agent1_credentials = vendor.get_agent_credentials(agent1_id)
        
        # Verify results
        assert len(agent1_credentials) == 2
        assert credential1 in agent1_credentials
        assert credential2 in agent1_credentials
        assert credential3 not in agent1_credentials
    
    def test_get_agent_credentials_expired(self):
        """Test that expired credentials aren't returned for an agent."""
        vendor = CredentialVendor()
        agent_id = uuid4()
        tool_id = uuid4()
        
        # Generate one credential that expires immediately
        credential1 = vendor.generate_credential(
            agent_id, 
            tool_id,
            duration=timedelta(milliseconds=1)
        )
        
        # Generate one credential that's valid for longer
        credential2 = vendor.generate_credential(
            agent_id, 
            tool_id,
            duration=timedelta(minutes=10)
        )
        
        # Wait for the first one to expire
        time.sleep(0.01)
        
        # Get credentials for the agent
        agent_credentials = vendor.get_agent_credentials(agent_id)
        
        # Only the non-expired credential should be returned
        assert len(agent_credentials) == 1
        assert credential2 in agent_credentials 