from pydantic import BaseModel
from typing import Dict, Any

# Define proper tool call event classes based on the AG-UI protocol
class ToolCallStartEvent(BaseModel):
    type: str = "TOOL_CALL_START"
    message_id: str
    toolCallId: str
    toolCallName: str
    tool: str
    delta: str = ""

class ToolCallArgsEvent(BaseModel):
    type: str = "TOOL_CALL_ARGS"
    message_id: str
    toolCallId: str
    toolCallName: str
    args: Dict[str, Any]
    delta: str = ""

class ToolCallEndEvent(BaseModel):
    type: str = "TOOL_CALL_END"
    message_id: str
    toolCallId: str
    toolCallName: str
    delta: str = ""
