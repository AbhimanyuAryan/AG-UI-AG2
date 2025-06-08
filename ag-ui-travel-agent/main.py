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

def check_dependencies():
    """Check if required dependencies are installed."""
    missing_deps = []
    
    try:
        import fastapi
    except ImportError:
        missing_deps.append("fastapi")
    
    try:
        import uvicorn
    except ImportError:
        missing_deps.append("uvicorn[standard]")
        
    try:
        import websockets
    except ImportError:
        missing_deps.append("websockets")
        
    try:
        import autogen
    except ImportError:
        missing_deps.append("pyautogen")
        
    try:
        import openai
    except ImportError:
        missing_deps.append("openai")
        
    if missing_deps:
        print("Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install them using:")
        print(f"pip install {' '.join(missing_deps)}")
        sys.exit(1)

def main():
    """Main entry point with dependency checking."""
    # Check dependencies first
    check_dependencies()
    
    try:
        import uvicorn
        
        print("Starting Travel Agent FastAPI Server...")
        print("- Server will run on: http://localhost:8000")
        print("- WebSocket endpoint: ws://localhost:8000/ws/{conversation_id}")
        print("- API endpoints available at: http://localhost:8000/docs")
        print("\nMake sure your React frontend is configured to connect to localhost:8000")
        
        # Use the import string instead of the app object for reload functionality
        uvicorn.run(
            "ag_ui_ag2.fastapi_ui:app",  # Import string instead of app object
            host="0.0.0.0", 
            port=8000, 
            reload=True,
            log_level="info"
        )
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("Please make sure all dependencies are installed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
