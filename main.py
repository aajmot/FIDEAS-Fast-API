#!/usr/bin/env python3
"""
FIDEAS API Server Startup Script
"""
import os
import sys
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def main():
    """Start the FIDEAS API server"""
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    reload = os.getenv("API_RELOAD", "True").lower() == "true"
    
    print(f"Starting FIDEAS API server on {host}:{port}")
    print(f"Reload mode: {reload}")
    print(f"API Documentation: http://{host}:{port}/docs")
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()