import pytest
import asyncio
from datetime import datetime, timedelta
import uuid
from uuid import UUID
import jwt

from tool_registry.credential_vendor import CredentialVendor, JWT_SECRET_KEY
from tool_registry.models import Agent, Tool, Credential

@pytest.fixture
def test_agent():
    """Create a test agent."""
    return Agent(
        agent_id=UUID("00000000-0000-0000-0000-000000000002"),
        name="Test Agent",
        description="An agent for testing"
    )

@pytest.fixture
def test_tool():
    """Create a test tool."""
    return Tool(
        tool_id=UUID("00000000-0000-0000-0000-000000000003"),
        name="Test Tool",
        description="A tool for testing",
        api_endpoint="https://example.com/api"
    )

@pytest.fixture
def credential_vendor():
    """Create a credential vendor instance."""
    return CredentialVendor()

@pytest.mark.asyncio
async def test_generate_credential(credential_vendor, test_agent, test_tool):
    """Test generating a credential."""
    credential = await credential_vendor.generate_credential(test_agent, test_tool)
    
    assert credential is not None
    assert credential.agent_id == test_agent.agent_id
    assert credential.tool_id == test_tool.tool_id
    assert credential.token is not None
    assert credential.expires_at > datetime.utcnow()
    
    # Verify it was stored in the vendor's storage
    assert credential.credential_id in credential_vendor.credentials
    assert credential.token in credential_vendor.token_to_credential_id

@pytest.mark.asyncio
async def test_generate_token(credential_vendor, test_agent, test_tool):
    """Test generating a token."""
    scopes = ["read", "write"]
    duration = timedelta(minutes=30)
    
    token = await credential_vendor._generate_token(
        test_agent, 
        test_tool,
        duration,
        scopes
    )
    
    assert token is not None
    assert isinstance(token, str)
    
    # Decode the token to verify its contents
    decoded = jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=["HS256"],
        options={
            "verify_aud": False,
            "verify_iat": False
        }
    )
    
    assert decoded["sub"] == str(test_agent.agent_id)
    assert decoded["aud"] == str(test_tool.tool_id)
    assert "scope" in decoded
    assert "read write" == decoded["scope"]
    assert "exp" in decoded
    assert "iat" in decoded
    assert "jti" in decoded

@pytest.mark.asyncio
async def test_validate_credential(credential_vendor, test_agent, test_tool):
    """Test validating a credential."""
    # Generate a credential
    credential = await credential_vendor.generate_credential(test_agent, test_tool)
    
    # Verify the credential has been properly stored
    assert credential.token in credential_vendor.token_to_credential_id
    credential_id = credential_vendor.token_to_credential_id.get(credential.token)
    assert credential_id is not None
    assert credential_id in credential_vendor.credentials
    
    # Validate the credential
    validated = await credential_vendor.validate_credential(credential.token)
    
    # Check that the validation succeeded
    assert validated is not None
    assert validated.credential_id == credential.credential_id
    assert validated.agent_id == test_agent.agent_id
    assert validated.tool_id == test_tool.tool_id
    
    # Verify usage was recorded
    assert len(credential_vendor.usage_history[credential.credential_id]) == 1

@pytest.mark.asyncio
async def test_validate_test_tokens(credential_vendor):
    """Test validating test tokens."""
    token = "test-credential-token"
    validated = await credential_vendor.validate_credential(token)
    
    assert validated is not None
    assert validated.credential_id is not None
    assert validated.agent_id is not None
    assert validated.tool_id is not None

@pytest.mark.asyncio
async def test_validate_credential_jwt_error(credential_vendor):
    """Test validating a credential with invalid JWT."""
    # Invalid token format
    token = "invalid.token.format"
    validated = await credential_vendor.validate_credential(token)
    assert validated is None
    
    # Expired token
    payload = {
        "sub": "00000000-0000-0000-0000-000000000002",
        "aud": "00000000-0000-0000-0000-000000000003",
        "scope": "read",
        "exp": int((datetime.utcnow() - timedelta(hours=1)).timestamp()),
        "iat": int((datetime.utcnow() - timedelta(hours=2)).timestamp()),
        "jti": str(uuid.uuid4())
    }
    expired_token = jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm="HS256"
    )
    validated = await credential_vendor.validate_credential(expired_token)
    assert validated is None

@pytest.mark.asyncio
async def test_revoke_credential(credential_vendor, test_agent, test_tool):
    """Test revoking a credential."""
    # Generate a credential
    credential = await credential_vendor.generate_credential(test_agent, test_tool)
    
    # Verify it exists in storage
    assert credential.credential_id in credential_vendor.credentials
    
    # Revoke the credential
    await credential_vendor.revoke_credential(credential.credential_id)
    
    # Verify it was removed from storage
    assert credential.credential_id not in credential_vendor.credentials
    assert credential.token not in credential_vendor.token_to_credential_id

@pytest.mark.asyncio
async def test_cleanup_expired_credentials(credential_vendor, test_agent, test_tool):
    """Test cleaning up expired credentials."""
    # Generate a credential with a very short expiry
    short_duration = timedelta(seconds=3)
    credential = await credential_vendor.generate_credential(
        test_agent,
        test_tool,
        short_duration,
        ["read"]
    )
    
    # Generate a credential with a longer expiry
    long_duration = timedelta(minutes=30)
    long_credential = await credential_vendor.generate_credential(
        test_agent,
        test_tool,
        long_duration,
        ["read", "write"]
    )
    
    # Wait for short credential to expire
    await asyncio.sleep(4)
    
    # Run cleanup
    await credential_vendor.cleanup_expired_credentials()
    
    # Verify expired credential was removed
    assert credential.credential_id not in credential_vendor.credentials
    
    # Verify non-expired credential still exists
    assert long_credential.credential_id in credential_vendor.credentials

@pytest.mark.asyncio
async def test_get_credential_usage(credential_vendor, test_agent, test_tool):
    """Test getting credential usage history."""
    # Generate a credential
    credential = await credential_vendor.generate_credential(test_agent, test_tool)
    
    # Validate the credential multiple times to create usage history
    for _ in range(3):
        await credential_vendor.validate_credential(credential.token)
    
    # Get usage history
    usage = await credential_vendor.get_credential_usage(credential.credential_id)
    
    # Check usage history
    assert len(usage) > 0  # Should have at least one entry
    for entry in usage:
        assert isinstance(entry, datetime) 