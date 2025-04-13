from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from .models import Tool, Agent, Policy, Credential
from .auth import authenticate_agent, create_access_token, get_current_agent
from .authorization import AuthorizationService
from .credential_vendor import CredentialVendor
from typing import List, Optional
from datetime import timedelta

app = FastAPI(
    title="GenAI Tool Registry",
    description="An open-source framework for managing GenAI tool access",
    version="0.1.0"
)

# Initialize services
auth_service = AuthorizationService()
credential_vendor = CredentialVendor()

# In-memory storage (replace with database in production)
tools = {}
agents = {}
policies = {}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    agent = await authenticate_agent(form_data.username, form_data.password)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": str(agent.agent_id)},
        expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/tools", response_model=Tool)
async def register_tool(
    tool: Tool,
    current_agent: Agent = Depends(get_current_agent)
):
    tools[str(tool.tool_id)] = tool
    return tool

@app.get("/tools", response_model=List[Tool])
async def list_tools(
    current_agent: Agent = Depends(get_current_agent)
):
    return list(tools.values())

@app.get("/tools/{tool_id}", response_model=Tool)
async def get_tool(
    tool_id: str,
    current_agent: Agent = Depends(get_current_agent)
):
    if tool_id not in tools:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tools[tool_id]

@app.post("/policies", response_model=Policy)
async def create_policy(
    policy: Policy,
    current_agent: Agent = Depends(get_current_agent)
):
    policies[str(policy.policy_id)] = policy
    auth_service.add_policy(policy)
    return policy

@app.post("/tools/{tool_id}/access")
async def request_tool_access(
    tool_id: str,
    current_agent: Agent = Depends(get_current_agent)
):
    if tool_id not in tools:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    tool = tools[tool_id]
    
    # Check authorization
    context = {}  # Add relevant context here
    if not await auth_service.check_access(current_agent, tool, context):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Generate temporary credential
    credential = await credential_vendor.generate_credential(
        agent=current_agent,
        tool=tool
    )
    
    return {
        "credential": credential,
        "tool": tool
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 