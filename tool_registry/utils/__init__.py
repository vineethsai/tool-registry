"""
Utility functions for the Tool Registry application.
"""

from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

import inspect
import logging
import functools
import uuid
from datetime import datetime

T = TypeVar('T')

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)

def add_context_to_logger(logger: logging.Logger, **context) -> logging.Logger:
    """Add context to a logger."""
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        for key, value in context.items():
            setattr(record, key, value)
        return record

    logging.setLogRecordFactory(record_factory)
    return logger

def log_function_call(func: Callable) -> Callable:
    """Decorator to log function calls."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        logger.debug(f"{func.__name__} returned {result}")
        return result
    return wrapper

# Import validation utilities safely
try:
    from .validation import (
        validate_uuid,
        validate_datetime,
        validate_url,
        validate_name,
    )
except ImportError:
    # Fallback implementations if validation module not available
    def validate_uuid(uuid_str: str) -> uuid.UUID:
        return uuid.UUID(uuid_str)
        
    def validate_datetime(dt_str: str) -> datetime:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        
    def validate_url(url: str) -> str:
        return url
        
    def validate_name(name: str, min_length: int = 3, max_length: int = 100) -> str:
        return name 