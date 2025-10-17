"""Session lifecycle management."""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import uuid

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import structlog

from .models import SessionContext, MessageRecord
from ..config import get_config
from ..logging.config import trace_function


logger = structlog.get_logger(__name__)


class SessionManager:
    """Manages session lifecycle and state."""

    def __init__(self):
        self.sessions: Dict[str, SessionContext] = {}
        self.config = get_config()

    def generate_id(self, prefix: str = "session") -> str:
        """Generate a unique ID."""
        return f"{prefix}_{uuid.uuid4().hex[:16]}"

    @trace_function
    async def create_session(
        self,
        title: Optional[str] = None,
        parent_id: Optional[str] = None,
        agent_name: str = "build",
    ) -> SessionContext:
        """Create a new session."""
        logger.debug("create_session_start", title=title, parent_id=parent_id, agent_name=agent_name)

        session_id = self.generate_id("session")
        logger.debug("create_session_id_generated", session_id=session_id)

        # Find agent config
        agent_config = next(
            (a for a in self.config.agents if a.name == agent_name),
            self.config.agents[0] if self.config.agents else None
        )

        if not agent_config:
            logger.error("create_session_no_agent", agent_name=agent_name)
            raise ValueError(f"No agent configuration found for '{agent_name}'")

        logger.debug("create_session_agent_found", agent_name=agent_name, model=agent_config.model)

        # Create session context
        session = SessionContext(
            id=session_id,
            project_id=self.config.project.id,
            directory=self.config.project.worktree,
            title=title or f"New session {session_id[:8]}",
            agent_name=agent_name,
            model=agent_config.model,
        )

        logger.debug("create_session_context_created", session_id=session_id, directory=session.directory)

        # Store parent relationship
        if parent_id:
            session.metadata["parentID"] = parent_id
            logger.debug("create_session_parent_set", session_id=session_id, parent_id=parent_id)

        # Create Claude SDK client
        options = ClaudeAgentOptions(
            allowed_tools=["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
            permission_mode="default",
            cwd=session.directory,
            model=session.model,
            include_partial_messages=True,  # For streaming updates
        )

        logger.debug("create_session_sdk_options_created", session_id=session_id, tools_count=6)

        session.client = ClaudeSDKClient(options=options)
        logger.debug("create_session_sdk_client_created", session_id=session_id)

        # Connect the client
        logger.debug("create_session_connecting_sdk", session_id=session_id)
        await session.client.connect()
        logger.debug("create_session_sdk_connected", session_id=session_id)

        # Store session
        self.sessions[session_id] = session
        logger.debug("create_session_stored", session_id=session_id, total_sessions=len(self.sessions))

        logger.info(
            "session_created",
            session_id=session_id,
            title=session.title,
            agent=agent_name,
            model=session.model,
        )

        return session

    @trace_function
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Get a session by ID."""
        session = self.sessions.get(session_id)
        logger.debug("get_session_lookup", session_id=session_id, found=session is not None)
        return session

    @trace_function
    def list_sessions(self) -> List[SessionContext]:
        """List all sessions."""
        sessions = list(self.sessions.values())
        logger.debug("list_sessions_result", count=len(sessions))
        return sessions

    @trace_function
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        logger.debug("delete_session_start", session_id=session_id)

        session = self.sessions.get(session_id)
        if not session:
            logger.debug("delete_session_not_found", session_id=session_id)
            return False

        # Disconnect client
        if session.client:
            try:
                logger.debug("delete_session_disconnecting_client", session_id=session_id)
                await session.client.disconnect()
                logger.debug("delete_session_client_disconnected", session_id=session_id)
            except Exception as e:
                logger.warning("session_disconnect_error", session_id=session_id, error=str(e), exception_type=type(e).__name__)

        # Remove from registry
        del self.sessions[session_id]
        logger.debug("delete_session_removed_from_registry", session_id=session_id, remaining_sessions=len(self.sessions))

        logger.info("session_deleted", session_id=session_id)
        return True

    @trace_function
    def update_session_metadata(
        self,
        session_id: str,
        **updates
    ) -> Optional[SessionContext]:
        """Update session metadata."""
        logger.debug("update_session_metadata_start", session_id=session_id, updates=updates)

        session = self.get_session(session_id)
        if not session:
            logger.debug("update_session_metadata_not_found", session_id=session_id)
            return None

        # Update allowed fields
        if "title" in updates:
            old_title = session.title
            session.title = updates["title"]
            logger.debug("update_session_metadata_title_changed", session_id=session_id, old_title=old_title, new_title=session.title)

        session.updated_at = int(datetime.now().timestamp() * 1000)
        session.metadata.update(updates)
        logger.debug("update_session_metadata_applied", session_id=session_id, updated_at=session.updated_at)

        logger.info("session_updated", session_id=session_id, updates=updates)
        return session

    @trace_function
    async def abort_session(self, session_id: str) -> bool:
        """Abort/cancel a running session operation."""
        logger.debug("abort_session_start", session_id=session_id)

        session = self.get_session(session_id)
        if not session or not session.client:
            logger.debug("abort_session_no_client", session_id=session_id, has_session=session is not None)
            return False

        try:
            logger.debug("abort_session_interrupting", session_id=session_id)
            await session.client.interrupt()
            logger.info("session_aborted", session_id=session_id)
            return True
        except Exception as e:
            logger.error("session_abort_error", session_id=session_id, error=str(e), exception_type=type(e).__name__)
            return False


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
