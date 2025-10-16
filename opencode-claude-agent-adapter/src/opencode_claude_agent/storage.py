"""In-memory storage for sessions and messages"""

import time
from typing import Dict, List, Optional
from .models import Session, Message, TimeInfo
import logging

logger = logging.getLogger(__name__)


class SessionStorage:
    """In-memory storage for sessions and messages"""

    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.messages: Dict[str, List[Message]] = {}  # session_id -> messages
        logger.info("Session storage initialized")

    def generate_id(self, prefix: str = "session") -> str:
        """Generate a time-based ID"""
        return f"{prefix}_{int(time.time() * 1000)}"

    def create_session(
        self,
        title: Optional[str] = None,
        directory: Optional[str] = None,
        project_id: str = "default_project"
    ) -> Session:
        """Create a new session"""
        session_id = self.generate_id("session")
        now = int(time.time() * 1000)

        session = Session(
            id=session_id,
            projectID=project_id,
            directory=directory or "/workspace",
            title=title or f"Session {session_id[:8]}",
            version="0.1.0",
            time=TimeInfo(created=now, updated=now)
        )

        self.sessions[session_id] = session
        self.messages[session_id] = []

        logger.info(f"Created session: {session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        return self.sessions.get(session_id)

    def get_all_sessions(self) -> List[Session]:
        """Get all sessions"""
        return list(self.sessions.values())

    def update_session(self, session_id: str, **updates) -> Optional[Session]:
        """Update session fields"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        now = int(time.time() * 1000)

        # Update allowed fields
        if "title" in updates:
            session.title = updates["title"]

        # Update timestamp
        session.time.updated = now

        logger.info(f"Updated session: {session_id}")
        return session

    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            if session_id in self.messages:
                del self.messages[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        return False

    def add_message(self, session_id: str, message: Message):
        """Add message to session"""
        if session_id not in self.messages:
            self.messages[session_id] = []

        self.messages[session_id].append(message)

        # Update session timestamp
        if session_id in self.sessions:
            self.sessions[session_id].time.updated = int(time.time() * 1000)

        logger.debug(f"Added message {message.info.id} to session {session_id}")

    def get_messages(self, session_id: str) -> List[Message]:
        """Get all messages for a session"""
        return self.messages.get(session_id, [])

    def get_message(self, session_id: str, message_id: str) -> Optional[Message]:
        """Get specific message"""
        messages = self.messages.get(session_id, [])
        for msg in messages:
            if msg.info.id == message_id:
                return msg
        return None
