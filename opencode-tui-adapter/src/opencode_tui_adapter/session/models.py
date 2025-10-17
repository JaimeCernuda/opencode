"""Data models for session management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from claude_agent_sdk import ClaudeSDKClient


@dataclass
class MessagePart:
    """A part of a message (text, tool, etc.)."""

    id: str
    type: str  # "text", "tool", "tool_result", etc.
    data: Dict[str, Any]


@dataclass
class MessageRecord:
    """A message in the conversation."""

    id: str
    session_id: str
    role: str  # "user" or "assistant"
    parts: List[MessagePart]
    created_at: int  # Unix timestamp in milliseconds
    completed_at: Optional[int] = None


@dataclass
class SessionContext:
    """Context for a single session."""

    id: str
    project_id: str
    directory: str
    title: str
    version: str = "0.1.0"
    created_at: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    updated_at: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))

    # Runtime state
    client: Optional[ClaudeSDKClient] = None
    messages: List[MessageRecord] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    agent_name: str = "build"
    model: str = "claude-3-5-sonnet-20241022"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "projectID": self.project_id,
            "directory": self.directory,
            "title": self.title,
            "version": self.version,
            "time": {
                "created": self.created_at,
                "updated": self.updated_at,
            },
            **self.metadata
        }
