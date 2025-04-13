from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from uuid import UUID
from ..core.auth import Agent

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_agent(token: str = Depends(oauth2_scheme)):
    """Get the current authenticated agent."""
    # Import here to avoid circular imports
    from ..api.app import auth_service
    
    agent = await auth_service.verify_token(token)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return agent 