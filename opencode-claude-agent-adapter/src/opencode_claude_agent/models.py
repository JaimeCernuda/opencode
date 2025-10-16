"""Data models for OpenCode TUI API"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class TimeInfo(BaseModel):
    """Timestamp information"""
    created: int
    updated: Optional[int] = None
    completed: Optional[int] = None


class Model(BaseModel):
    """Model configuration"""
    providerID: str
    modelID: str


class TextPart(BaseModel):
    """Text message part"""
    type: Literal["text"] = "text"
    text: str
    id: Optional[str] = None


class FilePart(BaseModel):
    """File reference part"""
    type: Literal["file"] = "file"
    path: str
    id: Optional[str] = None


class ToolUsePart(BaseModel):
    """Tool use part"""
    type: Literal["tool_use"] = "tool_use"
    id: str
    name: str
    input: Dict[str, Any]


class ToolResultPart(BaseModel):
    """Tool result part"""
    type: Literal["tool_result"] = "tool_result"
    tool_use_id: str
    content: str
    is_error: Optional[bool] = False


MessagePart = TextPart | FilePart | ToolUsePart | ToolResultPart


class MessageInfo(BaseModel):
    """Message metadata"""
    id: str
    sessionID: str
    role: Literal["user", "assistant"]
    time: TimeInfo


class Message(BaseModel):
    """Complete message with parts"""
    info: MessageInfo
    parts: List[MessagePart]


class SendMessageRequest(BaseModel):
    """Request to send a message"""
    messageID: str
    agent: str
    model: Model
    parts: List[MessagePart]


class Session(BaseModel):
    """Chat session"""
    id: str
    projectID: str
    directory: str
    title: str
    version: str = "0.1.0"
    parentID: Optional[str] = None
    time: TimeInfo
    share: Optional[Dict[str, str]] = None


class CreateSessionRequest(BaseModel):
    """Request to create a session"""
    title: Optional[str] = None
    directory: Optional[str] = None


class Project(BaseModel):
    """Project information"""
    id: str
    worktree: str
    vcs: str = "git"
    initialized: bool = True


class Config(BaseModel):
    """Configuration"""
    theme: str = "system"
    share: str = "disabled"
    model: str = ""
    keybinds: Dict[str, str] = Field(default_factory=lambda: {"leader": "ctrl+x"})
    tui: Dict[str, Any] = Field(default_factory=lambda: {"scrollSpeed": 3})


class Provider(BaseModel):
    """Model provider"""
    id: str
    name: str
    models: Dict[str, Dict[str, str]]


class ProvidersResponse(BaseModel):
    """Providers configuration"""
    providers: List[Provider]
    default: Dict[str, str]


class CommandRequest(BaseModel):
    """Slash command request"""
    command: str
    arguments: Optional[str] = None
    agent: str


class PathsResponse(BaseModel):
    """Filesystem paths"""
    state: str
    config: str
    worktree: str
    directory: str


class SSEEvent(BaseModel):
    """Server-Sent Event"""
    event: str = "message"
    data: Dict[str, Any]
    id: Optional[str] = None
