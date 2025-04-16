"""
Validation utilities for the tool registry.
"""

import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Union, get_type_hints

from pydantic import BaseModel, Field, validator
# For compatibility with newer pydantic versions
try:
    from pydantic.fields import ModelField
except ImportError:
    # For pydantic v2
    try:
        from pydantic.fields import FieldInfo as ModelField
    except ImportError:
        # Alternative for pydantic v2.6+
        from pydantic.json_schema import JsonSchemaValue as ModelField

T = TypeVar('T')

def validate_uuid(uuid_str: str) -> uuid.UUID:
    """Validate that a string is a valid UUID."""
    try:
        return uuid.UUID(uuid_str)
    except ValueError:
        raise ValueError(f"Invalid UUID format: {uuid_str}")

def validate_datetime(dt_str: str) -> datetime:
    """Validate that a string is a valid ISO datetime."""
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError(f"Invalid datetime format: {dt_str}")

def validate_url(url: str) -> str:
    """Validate that a string is a valid URL."""
    if not url.startswith(('http://', 'https://')):
        raise ValueError(f"URL must start with http:// or https://: {url}")
    return url

def validate_name(name: str, min_length: int = 3, max_length: int = 100) -> str:
    """Validate that a name string meets length requirements and doesn't contain special characters."""
    if len(name) < min_length:
        raise ValueError(f"Name must be at least {min_length} characters")
    if len(name) > max_length:
        raise ValueError(f"Name must be at most {max_length} characters")
    if re.search(r'[<>{}[\]"]', name):
        raise ValueError("Name contains invalid characters")
    return name 