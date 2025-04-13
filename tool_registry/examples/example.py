from uuid import UUID
from ..core.registry import Tool, ToolMetadata
from ..core.auth import AuthService
from ..core.credentials import CredentialVendor

def main():
    # Initialize services
    auth_service = AuthService(secret_key="example-secret-key")
    credential_vendor = CredentialVendor()
    
    # Create an agent
    agent = auth_service.create_agent(
        name="Example Agent",
        roles=["tool_user"],
        permissions=["register_tool", "access_tool:*"]
    )
    
    # Create a tool
    tool_metadata = ToolMetadata(
        name="example_tool",
        description="An example tool for demonstration",
        version="1.0.0",
        author="Example Author",
        tags=["example", "demo"],
        parameters={
            "input": "string",
            "count": "integer"
        },
        required_parameters=["input"],
        return_type="string"
    )
    
    tool = Tool(
        tool_metadata=tool_metadata,
        endpoint="https://api.example.com/tool",
        auth_required=True,
        auth_type="api_key",
        rate_limit=100,
        cost_per_call=0.01
    )
    
    # Register the tool
    tool_id = tool.tool_id
    
    # Request access to the tool
    credential = credential_vendor.generate_credential(
        agent_id=agent.agent_id,
        tool_id=tool_id,
        scopes=["read", "write"]
    )
    
    print(f"Agent created: {agent.name}")
    print(f"Tool registered: {tool.tool_metadata.name}")
    print(f"Credential generated: {credential.token}")
    print(f"Credential expires at: {credential.expires_at}")

if __name__ == "__main__":
    main() 