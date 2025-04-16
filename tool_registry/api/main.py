"""
Application entry point for the Tool Registry API.

This module imports and exposes the FastAPI app from app.py for use by ASGI servers like Uvicorn.
"""

from .app import app

__all__ = ["app"] 