from typing import List, Optional
from uuid import UUID
from .models import Agent, Policy, Tool

class PolicyEngine:
    """Core policy enforcement engine."""
    
    def __init__(self):
        self.policies = {}  # In-memory storage, replace with database in production
    
    async def evaluate_access(self, agent: Agent, tool: Tool, context: dict) -> bool:
        """
        Evaluate if an agent has access to a tool based on policies.
        
        Args:
            agent: The agent requesting access
            tool: The tool being accessed
            context: Additional context for policy evaluation
            
        Returns:
            bool: True if access is granted, False otherwise
        """
        # Get all relevant policies
        relevant_policies = [
            self.policies.get(policy_id)
            for policy_id in tool.policy_id
            if policy_id in self.policies
        ]
        
        # Evaluate each policy
        for policy in relevant_policies:
            if not policy:
                continue
                
            # Check role-based access
            if "roles" in policy.rules:
                if not any(role in policy.rules["roles"] for role in agent.roles):
                    return False
            
            # Check time-based restrictions
            if "time_restrictions" in policy.rules:
                if not self._check_time_restrictions(policy.rules["time_restrictions"]):
                    return False
            
            # Check resource limits
            if "resource_limits" in policy.rules:
                if not self._check_resource_limits(policy.rules["resource_limits"], context):
                    return False
        
        return True
    
    def _check_time_restrictions(self, restrictions: dict) -> bool:
        """Check if current time falls within allowed time windows."""
        # TODO: Implement time-based restrictions
        return True
    
    def _check_resource_limits(self, limits: dict, context: dict) -> bool:
        """Check if resource usage is within limits."""
        # TODO: Implement resource limit checks
        return True
    
    def add_policy(self, policy: Policy) -> None:
        """Add a new policy to the engine."""
        self.policies[policy.policy_id] = policy
    
    def remove_policy(self, policy_id: UUID) -> None:
        """Remove a policy from the engine."""
        if policy_id in self.policies:
            del self.policies[policy_id]

class AuthorizationService:
    """Service layer for authorization operations."""
    
    def __init__(self):
        self.policy_engine = PolicyEngine()
    
    async def check_access(self, agent: Agent, tool: Tool, context: dict) -> bool:
        """
        Check if an agent has access to a tool.
        
        Args:
            agent: The agent requesting access
            tool: The tool being accessed
            context: Additional context for policy evaluation
            
        Returns:
            bool: True if access is granted, False otherwise
        """
        return await self.policy_engine.evaluate_access(agent, tool, context)
    
    def add_policy(self, policy: Policy) -> None:
        """Add a new policy to the system."""
        self.policy_engine.add_policy(policy)
    
    def remove_policy(self, policy_id: UUID) -> None:
        """Remove a policy from the system."""
        self.policy_engine.remove_policy(policy_id) 