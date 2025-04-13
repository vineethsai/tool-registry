@pytest.mark.asyncio
async def test_validate_credential(credential_vendor, test_agent, test_tool):
    """Test validating a credential."""
    # Generate a credential
    credential = await credential_vendor.generate_credential(test_agent, test_tool)
    
    print(f"\nDEBUG: Generated credential with ID: {credential.credential_id}")
    print(f"DEBUG: Credential token: {credential.token[:20]}...")
    print(f"DEBUG: Stored credentials: {list(credential_vendor.credentials.keys())}")
    print(f"DEBUG: Token mapping: {credential_vendor.token_to_credential_id}")
    
    # Validate the credential
    validated = await credential_vendor.validate_credential(credential.token)
    
    # Check that the validation succeeded
    assert validated is not None
    assert validated.credential_id == credential.credential_id
    assert validated.agent_id == test_agent.agent_id
    assert validated.tool_id == test_tool.tool_id
    
    # Check that usage was recorded
    assert len(credential_vendor.usage_history[credential.credential_id]) == 1
    
    # Test with invalid token
    validated = await credential_vendor.validate_credential("invalid-token")
    assert validated is None
    
    # Test with expired token
    future_time = credential.expires_at + timedelta(seconds=1)
    validated = await credential_vendor.validate_credential(credential.token, current_time=future_time)
    assert validated is None
    
    # Old approach with patching
    # with patch('datetime.datetime') as mock_datetime:
    #     # Set current time to after expiration
    #     mock_datetime.utcnow.return_value = credential.expires_at + timedelta(seconds=1)
    #     
    #     validated = await credential_vendor.validate_credential(credential.token)
    #     assert validated is None 