#!/usr/bin/env python3
"""
Simple test script for Tool Registry API.
"""

import requests
import json
import uuid
import sys
from datetime import datetime, timedelta

# Base URL for API - change as needed
BASE_URL = "http://localhost:8000"

def test_register_tool():
    """Test tool registration."""
    # Generate a unique tool name to avoid conflicts
    unique_id = uuid.uuid4().hex[:8]
    
    tool_data = {
        "name": f"Test_Tool_{unique_id}",
        "description": "A test tool for testing the API",
        "version": "1.0.0",
        "tool_metadata": {
            "api_endpoint": "https://api.example.com/test",
            "auth_method": "API_KEY",
            "auth_config": {"header_name": "X-API-Key"},
            "params": {"query": {"type": "string"}},
            "tags": ["test", "api"]
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/tools", json=tool_data)
        print(f"Tool Registration Status: {response.status_code}")
        
        if response.status_code == 200:
            tool = response.json()
            print(f"✅ Successfully registered tool: {tool['name']} (ID: {tool['tool_id']})")
            return tool
        else:
            print(f"❌ Error registering tool: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception during tool registration: {str(e)}")
        return None

def test_get_tool(tool_id):
    """Test getting a tool by ID."""
    try:
        response = requests.get(f"{BASE_URL}/tools/{tool_id}")
        print(f"Get Tool Status: {response.status_code}")
        
        if response.status_code == 200:
            tool = response.json()
            print(f"✅ Successfully retrieved tool: {tool['name']} (ID: {tool['tool_id']})")
            return tool
        else:
            print(f"❌ Error retrieving tool: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception during tool retrieval: {str(e)}")
        return None

def test_create_credential():
    """Test credential creation."""
    try:
        # First get a test tool
        response = requests.get(f"{BASE_URL}/tools/00000000-0000-0000-0000-000000000003")
        if response.status_code != 200:
            print("❌ Could not retrieve test tool")
            return None
        
        tool = response.json()
        
        credential_data = {
            "agent_id": "00000000-0000-0000-0000-000000000001",
            "tool_id": tool["tool_id"],
            "credential_type": "API_KEY",
            "credential_value": {"key": "test-api-key"},
            "scope": ["read", "write"],
            "expires_at": (datetime.utcnow() + timedelta(days=1)).isoformat()
        }
        
        response = requests.post(f"{BASE_URL}/credentials", json=credential_data)
        print(f"Create Credential Status: {response.status_code}")
        
        if response.status_code == 200:
            credential = response.json()
            print(f"✅ Successfully created credential: {credential['credential_id']}")
            print(f"   Token: {credential.get('token', 'N/A')}")
            print(f"   Scopes: {credential.get('scope', [])}")
            print(f"   Expires: {credential.get('expires_at', 'N/A')}")
            return credential
        else:
            print(f"❌ Error creating credential: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception during credential creation: {str(e)}")
        return None

def run_tests():
    """Run all tests."""
    print("\n=== Testing Tool Registry API ===")
    print(f"API URL: {BASE_URL}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check: API is up and running")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print("Aborting tests as API is not available")
            return
    except Exception as e:
        print(f"❌ Health check exception: {str(e)}")
        print("Aborting tests as API is not available")
        return
    
    # Test tool registration
    print("\n--- Testing Tool Registration ---")
    tool = test_register_tool()
    
    if tool:
        # Test getting the tool by ID
        print("\n--- Testing Get Tool by ID ---")
        retrieved_tool = test_get_tool(tool["tool_id"])
        
        # Test getting the tool again to verify consistency
        if retrieved_tool:
            print("\n--- Verifying Tool Consistency ---")
            if retrieved_tool["name"] == tool["name"]:
                print(f"✅ Tool name consistency verified: {retrieved_tool['name']}")
            else:
                print(f"❌ Tool name mismatch: {tool['name']} vs {retrieved_tool['name']}")
    
    # Test credential creation
    print("\n--- Testing Credential Creation ---")
    credential = test_create_credential()
    
    print("\n=== Tests Complete ===")
    
    # Return success status
    if tool and credential:
        return True
    return False

if __name__ == "__main__":
    success = run_tests()
    # Exit with appropriate status code
    sys.exit(0 if success else 1) 