"""Unit tests for session manager."""

import pytest
from opencode_tui_adapter.session.manager import SessionManager


@pytest.mark.asyncio
async def test_create_session():
    """Test session creation."""
    manager = SessionManager()

    session = await manager.create_session(title="Test Session")

    assert session is not None
    assert session.id.startswith("session_")
    assert session.title == "Test Session"
    assert session.client is not None


@pytest.mark.asyncio
async def test_get_session():
    """Test session retrieval."""
    manager = SessionManager()

    session = await manager.create_session()
    retrieved = manager.get_session(session.id)

    assert retrieved is not None
    assert retrieved.id == session.id


@pytest.mark.asyncio
async def test_list_sessions():
    """Test listing sessions."""
    manager = SessionManager()

    session1 = await manager.create_session(title="Session 1")
    session2 = await manager.create_session(title="Session 2")

    sessions = manager.list_sessions()

    assert len(sessions) >= 2
    session_ids = [s.id for s in sessions]
    assert session1.id in session_ids
    assert session2.id in session_ids


@pytest.mark.asyncio
async def test_delete_session():
    """Test session deletion."""
    manager = SessionManager()

    session = await manager.create_session()
    success = await manager.delete_session(session.id)

    assert success is True
    assert manager.get_session(session.id) is None


@pytest.mark.asyncio
async def test_delete_nonexistent_session():
    """Test deleting non-existent session."""
    manager = SessionManager()

    success = await manager.delete_session("nonexistent")

    assert success is False


@pytest.mark.asyncio
async def test_update_session_metadata():
    """Test updating session metadata."""
    manager = SessionManager()

    session = await manager.create_session(title="Original Title")
    updated = manager.update_session_metadata(session.id, title="Updated Title")

    assert updated is not None
    assert updated.title == "Updated Title"
    assert updated.id == session.id


@pytest.mark.asyncio
async def test_session_to_dict():
    """Test session serialization."""
    manager = SessionManager()

    session = await manager.create_session(title="Test Session")
    data = session.to_dict()

    assert data["id"] == session.id
    assert data["projectID"] == session.project_id
    assert data["directory"] == session.directory
    assert data["title"] == "Test Session"
    assert "time" in data
    assert "created" in data["time"]
    assert "updated" in data["time"]
