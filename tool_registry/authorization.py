"""
Authorization module for the Tool Registry system.

This module provides the core authorization functionality, including policy evaluation
and access control decisions. It implements a flexible policy-based authorization system
that supports role-based access control, time-based restrictions, and resource limits.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .models import Agent, Tool, Policy, AccessLog
import logging
import uuid

logger = logging.getLogger(__name__)

class AuthorizationService:
    """
    Service for managing authorization and access control.
    
    This service handles policy evaluation, access control decisions, and policy management.
    It supports role-based access control, time-based restrictions, and resource limits.
    """
    
    def __init__(self):
        """Initialize the authorization service with empty policy store."""
        self.policies: Dict[str, Policy] = {}
        self.access_logs: List[AccessLog] = []
    
    async def evaluate_access(
        self,
        agent: Agent,
        tool: Tool,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate access for an agent to a tool based on policies.
        
        Args:
            agent: The agent requesting access
            tool: The tool being accessed
            context: Additional context for policy evaluation
            
        Returns:
            Dictionary containing access decision and details
        """
        logger.info(f"Evaluating access for agent {agent.agent_id} to tool {tool.tool_id}")
        
        # Check if agent is admin
        if "admin" in agent.roles:
            logger.info(f"Admin access granted for agent {agent.agent_id}")
            return {
                "granted": True,
                "reason": "Admin access granted",
                "scopes": ["read", "write", "execute", "admin"],
                "duration_minutes": 60
            }
        
        # Get relevant policies
        relevant_policies = []
        if hasattr(tool, 'policies') and tool.policies:
            for policy in tool.policies:
                policy_id = str(policy.policy_id)
                if policy_id in self.policies:
                    # Use the policy from our store, not the one from the relationship
                    relevant_policies.append(self.policies[policy_id])
                else:
                    # If not in our store yet, add it
                    self.policies[policy_id] = policy
                    relevant_policies.append(policy)
        
        logger.info(f"Found {len(relevant_policies)} relevant policies for tool {tool.tool_id}")
        
        # If no policies are defined, grant access for testing
        if not relevant_policies:
            logger.info(f"No policies defined for tool {tool.tool_id}, granting test access")
            return {
                "granted": True,
                "reason": "No policies defined",
                "scopes": ["read", "write", "execute"],
                "duration_minutes": 30
            }
        
        # Evaluate each policy
        for policy in relevant_policies:
            if not self._policy_applies(policy, agent, tool):
                logger.debug(f"Policy {policy.policy_id} does not apply to agent {agent.agent_id}")
                continue
            
            policy_result = self._evaluate_policy_rules(policy, agent, tool, context)
            if policy_result["granted"]:
                logger.info(f"Access granted by policy {policy.policy_id} for agent {agent.agent_id}")
                return policy_result
        
        logger.info(f"No applicable policies found for agent {agent.agent_id}")
        return {
            "granted": False,
            "reason": "No applicable policies found",
            "scopes": [],
            "duration_minutes": 0
        }
    
    def _policy_applies(self, policy: Policy, agent: Agent, tool: Tool) -> bool:
        """
        Check if a policy applies to the given agent and tool.
        
        Args:
            policy: The policy to check
            agent: The agent to check against
            tool: The tool to check against
            
        Returns:
            True if the policy applies, False otherwise
        """
        rules = policy.rules
        
        # Check roles
        if "roles" in rules and not any(role in agent.roles for role in rules["roles"]):
            logger.info(f"Policy {policy.policy_id} does not apply due to roles mismatch: agent roles {agent.roles}, policy requires one of {rules['roles']}")
            return False
        
        # Check tool IDs
        if "tool_ids" in rules and str(tool.tool_id) not in rules["tool_ids"]:
            logger.info(f"Policy {policy.policy_id} does not apply due to tool ID mismatch: tool ID {tool.tool_id}, policy requires one of {rules['tool_ids']}")
            return False
        
        # Check tool tags
        if "tool_tags" in rules and not any(tag in tool.tags for tag in rules["tool_tags"]):
            logger.info(f"Policy {policy.policy_id} does not apply due to tool tags mismatch: tool tags {tool.tags}, policy requires one of {rules['tool_tags']}")
            return False
        
        logger.info(f"Policy {policy.policy_id} applies to agent {agent.agent_id} and tool {tool.tool_id}")
        return True
    
    def _evaluate_policy_rules(
        self,
        policy: Policy,
        agent: Agent,
        tool: Tool,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate the rules of a policy.
        
        Args:
            policy: The policy to evaluate
            agent: The agent to evaluate against
            tool: The tool to evaluate against
            context: Additional context for evaluation
            
        Returns:
            Dictionary containing policy evaluation result
        """
        rules = policy.rules
        current_time = datetime.utcnow()
        context = context or {}
        
        # Check time restrictions
        if "time_restrictions" in rules:
            restrictions = rules["time_restrictions"]
            if not self._check_time_restrictions(restrictions, current_time):
                logger.info(f"Time-based restrictions denied access for policy {policy.policy_id}")
                return {
                    "granted": False,
                    "reason": "Access denied due to time restrictions",
                    "scopes": [],
                    "duration_minutes": 0
                }
        
        # Check resource limits
        if "resource_limits" in rules:
            limits = rules["resource_limits"]
            logger.info(f"Found resource limits in policy: {limits}")
            
            # Check call rate limits
            if "max_calls_per_minute" in limits and "call_history" in context:
                call_history = context["call_history"]
                now = datetime.utcnow()
                # Count calls in the last minute
                recent_calls = [t for t in call_history if now - t < timedelta(minutes=1)]
                logger.info(f"Recent calls: {len(recent_calls)}, max allowed: {limits['max_calls_per_minute']}")
                
                if len(recent_calls) >= limits["max_calls_per_minute"]:
                    logger.info(f"Call rate limit exceeded for policy {policy.policy_id}")
                    return {
                        "granted": False,
                        "reason": "Access denied due to resource limits",
                        "scopes": [],
                        "duration_minutes": 0
                    }
            
            # Check request count limits
            if "max_requests" in limits and agent.request_count >= limits["max_requests"]:
                logger.info(f"Request count limit exceeded for policy {policy.policy_id}")
                return {
                    "granted": False,
                    "reason": "Access denied due to resource limits",
                    "scopes": [],
                    "duration_minutes": 0
                }
        
        # Default grant with policy scopes
        allowed_scopes = rules.get("allowed_scopes", ["read"])
        
        return {
            "granted": True,
            "reason": f"Access granted by policy {policy.name}",
            "scopes": allowed_scopes,
            "duration_minutes": rules.get("duration_minutes", 30)
        }
    
    def _check_time_restrictions(self, restrictions: dict, current_time: datetime) -> bool:
        """
        Check if current time falls within allowed time windows.
        
        Args:
            restrictions: Time restriction rules
            current_time: Current time to check against
            
        Returns:
            True if time is allowed, False otherwise
        """
        # Check day restrictions
        if "allowed_days" in restrictions:
            current_day = current_time.weekday()
            if current_day not in restrictions["allowed_days"]:
                return False
        
        # Check hour restrictions
        if "allowed_hours" in restrictions:
            current_hour = current_time.hour
            for start_hour, end_hour in restrictions["allowed_hours"]:
                if start_hour <= current_hour < end_hour:
                    return True
            return False
        
        return True
    
    async def check_access(
        self,
        agent: Agent,
        tool: Tool,
        scopes: List[str]
    ) -> Dict[str, Any]:
        """
        Check if an agent has access to a tool with the requested scopes.
        
        Args:
            agent: The agent requesting access
            tool: The tool being accessed
            scopes: The requested access scopes
            
        Returns:
            Dictionary containing access decision and details
        """
        result = await self.evaluate_access(agent, tool)
        
        if not result["granted"]:
            return result
        
        # Check if requested scopes are allowed
        if not all(scope in result["scopes"] for scope in scopes):
            return {
                "granted": False,
                "reason": "Requested scopes not allowed",
                "scopes": [],
                "duration_minutes": 0
            }
        
        return result
    
    async def add_policy(self, policy: Policy) -> None:
        """
        Add a new policy to the authorization service.
        
        Args:
            policy: The policy to add
        """
        self.policies[str(policy.policy_id)] = policy
    
    async def remove_policy(self, policy_id: str) -> None:
        """
        Remove a policy from the authorization service.
        
        Args:
            policy_id: The ID of the policy to remove
        """
        if policy_id in self.policies:
            del self.policies[policy_id]
    
    async def get_policy(self, policy_id: str) -> Optional[Policy]:
        """
        Get a policy by its ID.
        
        Args:
            policy_id: The ID of the policy to retrieve
            
        Returns:
            The requested policy, or None if not found
        """
        return self.policies.get(policy_id)
    
    async def list_policies(self) -> List[Policy]:
        """
        List all policies in the authorization service.
        
        Returns:
            List of all policies
        """
        return list(self.policies.values())
    
    async def get_access_logs(self) -> List[AccessLog]:
        """
        Get all access logs.
        
        Returns:
            List of all access logs
        """
        return self.access_logs
    
    async def log_access(
        self,
        agent: Agent,
        tool: Tool,
        credential_id: str,
        access_granted: bool,
        reason: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an access attempt.
        
        Args:
            agent: The agent that attempted access
            tool: The tool being accessed
            credential_id: The ID of the credential used
            access_granted: Whether the access was granted
            reason: Reason for access decision
            request_data: Optional request data
        """
        log_entry = AccessLog(
            log_id=uuid.uuid4(),
            agent_id=agent.agent_id,
            tool_id=tool.tool_id,
            credential_id=credential_id,
            access_granted=access_granted,
            reason=reason,
            request_data=request_data or {}
        )
        self.access_logs.append(log_entry) 