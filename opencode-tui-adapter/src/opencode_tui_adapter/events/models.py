"""Event data models."""

from dataclasses import dataclass
from typing import Any, Dict, Literal


EventType = Literal[
    "server.connected",
    "session.updated",
    "message.updated",
    "message.part.updated",
    "session.error",
    "permission.requested",
]


@dataclass
class Event:
    """An event to broadcast via SSE."""

    type: EventType
    properties: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for SSE."""
        return {
            "type": self.type,
            "properties": self.properties,
        }
