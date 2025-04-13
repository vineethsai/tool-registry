"""
Monitoring module for the Tool Registry system.

This module provides monitoring and logging functionality for the Tool Registry system,
including request tracking, error logging, and access logging.
"""

import logging
import time
from typing import Callable, Any, Dict, Optional
from functools import wraps
from prometheus_client import Counter, Histogram, start_http_server
from datetime import datetime
from uuid import UUID

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("tool_registry")

# Prometheus metrics
REQUEST_COUNT = Counter(
    "tool_registry_requests_total",
    "Total number of requests",
    ["endpoint", "method", "status"]
)

REQUEST_LATENCY = Histogram(
    "tool_registry_request_latency_seconds",
    "Request latency in seconds",
    ["endpoint", "method"]
)

ERROR_COUNT = Counter(
    "tool_registry_errors_total",
    "Total number of errors",
    ["endpoint", "method", "error_type"]
)

class Monitoring:
    def __init__(self, prometheus_port: int = 8000):
        self.prometheus_port = prometheus_port
    
    def start(self):
        """Start the Prometheus metrics server."""
        start_http_server(self.prometheus_port)
        logger.info(f"Prometheus metrics server started on port {self.prometheus_port}")
    
    def log_request(self, endpoint: str, method: str, status: int):
        """Log a request."""
        REQUEST_COUNT.labels(endpoint=endpoint, method=method, status=status).inc()
    
    def log_error(self, endpoint: str, method: str, error_type: str):
        """Log an error."""
        ERROR_COUNT.labels(endpoint=endpoint, method=method, error_type=error_type).inc()
        logger.error(f"Error in {method} {endpoint}: {error_type}")
    
    def measure_latency(self, endpoint: str, method: str):
        """Measure request latency."""
        return REQUEST_LATENCY.labels(endpoint=endpoint, method=method).time()

def monitor_request(func=None, endpoint=None):
    """Decorator to monitor API requests.
    
    This can be used either as @monitor_request or @monitor_request(endpoint='path')
    """
    if func is None:
        # Called with parameters: @monitor_request(endpoint='path')
        def decorator(f):
            @wraps(f)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                method = f.__name__.upper()
                endpoint_path = endpoint or f.__name__
                
                try:
                    result = await f(*args, **kwargs)
                    status = 200
                    return result
                except Exception as e:
                    status = 500
                    monitoring.log_error(endpoint_path, method, str(e))
                    raise
                finally:
                    latency = time.time() - start_time
                    monitoring.log_request(endpoint_path, method, status)
                    logger.info(f"{method} {endpoint_path} - {status} - {latency:.2f}s")
            
            return wrapper
        return decorator
    else:
        # Called without parameters: @monitor_request
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            method = func.__name__.upper()
            endpoint_path = func.__name__
            
            try:
                result = await func(*args, **kwargs)
                status = 200
                return result
            except Exception as e:
                status = 500
                monitoring.log_error(endpoint_path, method, str(e))
                raise
            finally:
                latency = time.time() - start_time
                monitoring.log_request(endpoint_path, method, status)
                logger.info(f"{method} {endpoint_path} - {status} - {latency:.2f}s")
        
        return wrapper

# Initialize monitoring
monitoring = Monitoring()

async def log_access(
    agent_id: UUID,
    tool_id: str,
    action: str,
    status: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an access attempt to a tool.
    
    Args:
        agent_id: The ID of the agent attempting access
        tool_id: The ID of the tool being accessed
        action: The action being performed (e.g., "ACCESS_REQUEST", "VALIDATE_ACCESS")
        status: The status of the access attempt (e.g., "GRANTED", "DENIED")
        details: Additional details about the access attempt
    """
    log_message = f"Access attempt - Agent: {agent_id}, Tool: {tool_id}, Action: {action}, Status: {status}"
    if details:
        log_message += f", Details: {details}"
    
    logger.info(log_message)
    
    # Update metrics
    monitoring.log_request(f"/tools/{tool_id}/access", "POST", 200 if status == "GRANTED" else 403) 