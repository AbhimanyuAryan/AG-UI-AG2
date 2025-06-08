"""
Simple runner without reload functionality.
Use this if you're having issues with the main.py reload feature.
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.ag_ui_ag2.fastapi_ui import app
import uvicorn

if __name__ == "__main__":
    print("Starting Travel Agent FastAPI Server (Simple Mode)...")
    print("- Server will run on: http://localhost:8000")
    print("- WebSocket endpoint: ws://localhost:8000/ws/{conversation_id}")
    print("- API endpoints available at: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
