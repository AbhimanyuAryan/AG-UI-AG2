"""
Main entry point for the FastAPI-based travel agent server.
This replaces the AG-UI adapter with a custom FastAPI implementation.
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import the FastAPI app
from ag_ui_ag2.fastapi_ui import app

if __name__ == "__main__":
    import uvicorn
    
    print("Starting Travel Agent FastAPI Server...")
    print("- Server will run on: http://localhost:8000")
    print("- WebSocket endpoint: ws://localhost:8000/ws/{conversation_id}")
    print("- API endpoints available at: http://localhost:8000/docs")
    print("\nMake sure your React frontend is configured to connect to localhost:8000")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
