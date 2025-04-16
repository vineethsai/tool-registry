#!/usr/bin/env python3
"""
Script to run the Tool Registry API server.
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Default configuration
HOST = os.getenv("API_HOST", "0.0.0.0")
PORT = int(os.getenv("API_PORT", 8000))
RELOAD = os.getenv("API_RELOAD", "true").lower() == "true"

if __name__ == "__main__":
    print(f"Starting Tool Registry API server on {HOST}:{PORT}")
    print(f"Auto-reload: {'enabled' if RELOAD else 'disabled'}")
    
    uvicorn.run(
        "tool_registry.api.app:app",
        host=HOST,
        port=PORT,
        reload=RELOAD
    ) 