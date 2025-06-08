import asyncio
import json
import threading
import uuid
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse
    from fastapi import Request
    import uvicorn
except ImportError as e:
    print(f"FastAPI dependencies not found: {e}")
    print("Please install: pip install fastapi uvicorn[standard] websockets")
    raise

# Simple event types for our protocol
class EventType(str, Enum):
    MESSAGE = "message"
    INPUT_REQUEST = "input_request"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    CONVERSATION_END = "conversation_end"
    ERROR = "error"

@dataclass
class UIEvent:
    type: EventType
    data: Dict[str, Any]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))

class ConversationManager:
    """Manages active conversations and their state"""
    
    def __init__(self):
        self.conversations: Dict[str, Dict] = {}
        self.websockets: Dict[str, WebSocket] = {}
        self.pending_inputs: Dict[str, asyncio.Queue] = {}
        logger.info("ConversationManager initialized")
    
    def create_conversation(self, conversation_id: str) -> None:
        """Initialize a new conversation"""
        logger.info(f"Creating conversation: {conversation_id}")
        self.conversations[conversation_id] = {
            "id": conversation_id,
            "status": "active",
            "messages": [],
            "created_at": datetime.now().isoformat()
        }
        self.pending_inputs[conversation_id] = asyncio.Queue()
        logger.info(f"Conversation created successfully: {conversation_id}")
    
    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        """Add a message to the conversation"""
        logger.debug(f"Adding message to conversation {conversation_id}: role={role}, content={content[:100]}...")
        if conversation_id in self.conversations:
            message = {
                "id": str(uuid.uuid4()),
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            self.conversations[conversation_id]["messages"].append(message)
            logger.debug(f"Message added successfully to conversation {conversation_id}")
        else:
            logger.error(f"Conversation {conversation_id} not found when adding message")
    
    async def send_event(self, conversation_id: str, event: UIEvent) -> None:
        """Send an event to the connected WebSocket"""
        logger.debug(f"Sending event to conversation {conversation_id}: {event.type}")
        if conversation_id in self.websockets:
            try:
                event_json = event.to_json()
                logger.debug(f"Event JSON: {event_json}")
                await self.websockets[conversation_id].send_text(event_json)
                logger.debug(f"Event sent successfully to {conversation_id}")
            except Exception as e:
                logger.error(f"Error sending event to {conversation_id}: {e}")
        else:
            logger.warning(f"No WebSocket found for conversation {conversation_id}")
    
    async def wait_for_input(self, conversation_id: str) -> str:
        """Wait for user input"""
        logger.info(f"Waiting for input from conversation {conversation_id}")
        if conversation_id in self.pending_inputs:
            try:
                result = await self.pending_inputs[conversation_id].get()
                logger.info(f"Received input from conversation {conversation_id}: {result}")
                return result
            except Exception as e:
                logger.error(f"Error waiting for input from {conversation_id}: {e}")
                return ""
        logger.error(f"No input queue found for conversation {conversation_id}")
        return ""
    
    async def provide_input(self, conversation_id: str, user_input: str) -> None:
        """Provide user input to waiting conversation"""
        logger.info(f"Providing input to conversation {conversation_id}: {user_input}")
        if conversation_id in self.pending_inputs:
            try:
                await self.pending_inputs[conversation_id].put(user_input)
                logger.info(f"Input provided successfully to conversation {conversation_id}")
            except Exception as e:
                logger.error(f"Error providing input to {conversation_id}: {e}")
        else:
            logger.error(f"No input queue found for conversation {conversation_id}")

# Global conversation manager
conversation_manager = ConversationManager()

class FastAPITravelUI:
    """UI implementation that interfaces with our travel workflow"""
    
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        logger.info(f"FastAPITravelUI initialized for conversation: {conversation_id}")
    
    async def text_input(self, sender: str, recipient: str, prompt: str) -> str:
        """Request text input from user via WebSocket"""
        logger.info(f"[UI] text_input called - sender: {sender}, recipient: {recipient}")
        logger.info(f"[UI] Prompt: {prompt}")
        
        # Send input request event
        event = UIEvent(
            type=EventType.INPUT_REQUEST,
            data={
                "sender": sender,
                "recipient": recipient,
                "prompt": prompt,
                "conversation_id": self.conversation_id
            }
        )
        
        logger.info(f"[UI] Sending input request event for conversation {self.conversation_id}")
        await conversation_manager.send_event(self.conversation_id, event)
        
        # Wait for user response
        logger.info(f"[UI] Waiting for user response...")
        response = await conversation_manager.wait_for_input(self.conversation_id)
        logger.info(f"[UI] Received user response: {response}")
        
        # Add both prompt and response to conversation
        conversation_manager.add_message(self.conversation_id, "assistant", prompt)
        conversation_manager.add_message(self.conversation_id, "user", response)
        
        return response
    
    async def process_messages(self, messages: List[Dict]) -> str:
        """Process and display conversation messages"""
        logger.info(f"[UI] process_messages called with {len(messages)} messages")
        for i, msg in enumerate(messages):
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
            
            logger.debug(f"[UI] Processing message {i}: role={role}, content={content[:100]}...")
            
            if content:  # Only send non-empty messages
                event = UIEvent(
                    type=EventType.MESSAGE,
                    data={
                        "role": role,
                        "content": content,
                        "conversation_id": self.conversation_id
                    }
                )
                await conversation_manager.send_event(self.conversation_id, event)
                conversation_manager.add_message(self.conversation_id, role, content)
        
        logger.info(f"[UI] Finished processing {len(messages)} messages")
        return "Messages processed"

def create_fastapi_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    logger.info("Creating FastAPI application")
    app = FastAPI(title="Travel Agent API", version="1.0.0")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # React app URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware added")
    
    @app.websocket("/ws/{conversation_id}")
    async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
        """WebSocket endpoint for real-time communication"""
        logger.info(f"WebSocket connection request for conversation: {conversation_id}")
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for conversation: {conversation_id}")
        
        conversation_manager.websockets[conversation_id] = websocket
        conversation_manager.create_conversation(conversation_id)
        
        try:
            while True:
                # Listen for messages from client
                logger.debug(f"Waiting for WebSocket message from {conversation_id}")
                data = await websocket.receive_text()
                logger.info(f"Received WebSocket data from {conversation_id}: {data}")
                
                try:
                    message_data = json.loads(data)
                    logger.debug(f"Parsed message data: {message_data}")
                    
                    if message_data.get("type") == "user_input":
                        # User provided input
                        user_input = message_data.get("content", "")
                        logger.info(f"User input received from {conversation_id}: {user_input}")
                        await conversation_manager.provide_input(conversation_id, user_input)
                    else:
                        logger.warning(f"Unknown message type from {conversation_id}: {message_data.get('type')}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON from {conversation_id}: {e}")
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for conversation: {conversation_id}")
            # Clean up when client disconnects
            if conversation_id in conversation_manager.websockets:
                del conversation_manager.websockets[conversation_id]
            if conversation_id in conversation_manager.pending_inputs:
                del conversation_manager.pending_inputs[conversation_id]
        except Exception as e:
            logger.error(f"WebSocket error for conversation {conversation_id}: {e}")
    
    @app.post("/api/start_conversation")
    async def start_conversation(request: dict):
        """Start a new travel planning conversation"""
        logger.info(f"Starting new conversation with request: {request}")
        conversation_id = str(uuid.uuid4())
        logger.info(f"Generated conversation ID: {conversation_id}")
        
        # Import and run the workflow in background
        try:
            logger.info("Importing workflow module...")
            from .without_fastagency import hitl_workflow
            logger.info("Workflow module imported successfully")
        except Exception as e:
            logger.error(f"Error importing workflow: {e}")
            raise HTTPException(status_code=500, detail=f"Error importing workflow: {e}")
        
        async def run_workflow():
            logger.info(f"Starting workflow execution for conversation {conversation_id}")
            try:
                ui = FastAPITravelUI(conversation_id)
                logger.info("FastAPITravelUI created")
                
                initial_message = request.get("initial_message", "Hi, I need help planning a trip")
                logger.info(f"Running workflow with initial message: {initial_message}")
                
                # Run the workflow with the FastAPI UI
                await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: hitl_workflow(initial_message, ui)
                )
                
                logger.info(f"Workflow execution completed for conversation {conversation_id}")
                
                # Send conversation end event
                event = UIEvent(
                    type=EventType.CONVERSATION_END,
                    data={"conversation_id": conversation_id}
                )
                await conversation_manager.send_event(conversation_id, event)
                logger.info(f"Conversation end event sent for {conversation_id}")
                
            except Exception as e:
                logger.error(f"Error in workflow execution for {conversation_id}: {e}", exc_info=True)
                # Send error event
                event = UIEvent(
                    type=EventType.ERROR,
                    data={
                        "error": str(e),
                        "conversation_id": conversation_id
                    }
                )
                await conversation_manager.send_event(conversation_id, event)
        
        # Start workflow in background
        logger.info("Creating background task for workflow")
        task = asyncio.create_task(run_workflow())
        logger.info(f"Background task created: {task}")
        
        return {"conversation_id": conversation_id}
    
    @app.get("/api/conversation/{conversation_id}")
    async def get_conversation(conversation_id: str):
        """Get conversation history"""
        logger.info(f"Getting conversation history for: {conversation_id}")
        if conversation_id in conversation_manager.conversations:
            logger.info(f"Conversation found: {conversation_id}")
            return conversation_manager.conversations[conversation_id]
        logger.warning(f"Conversation not found: {conversation_id}")
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    @app.get("/")
    async def root():
        """Root endpoint with basic info"""
        logger.info("Root endpoint accessed")
        return {
            "message": "Travel Agent FastAPI Server",
            "endpoints": {
                "websocket": "/ws/{conversation_id}",
                "start_conversation": "/api/start_conversation",
                "docs": "/docs"
            }
        }
    
    logger.info("FastAPI application created successfully")
    return app

# Create the app instance
app = create_fastapi_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
