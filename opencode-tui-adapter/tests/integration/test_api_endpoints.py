"""Integration tests for API endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from opencode_tui_adapter.server import app


@pytest.mark.asyncio
async def test_get_project():
    """Test project endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/project/current")
        assert response.status_code == 200

        project = response.json()
        assert "id" in project
        assert "worktree" in project
        assert "vcs" in project


@pytest.mark.asyncio
async def test_list_agents():
    """Test agents endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/agent")
        assert response.status_code == 200

        agents = response.json()
        assert isinstance(agents, list)
        assert len(agents) > 0
        assert "name" in agents[0]


@pytest.mark.asyncio
async def test_get_paths():
    """Test paths endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/path")
        assert response.status_code == 200

        paths = response.json()
        assert "state" in paths
        assert "config" in paths
        assert "worktree" in paths


@pytest.mark.asyncio
async def test_get_config():
    """Test config endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/config")
        assert response.status_code == 200

        config = response.json()
        assert "theme" in config


@pytest.mark.asyncio
async def test_list_providers():
    """Test providers endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/config/providers")
        assert response.status_code == 200

        data = response.json()
        assert "providers" in data
        assert "default" in data


@pytest.mark.asyncio
async def test_create_and_get_session():
    """Test session creation and retrieval."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create session
        response = await client.post("/session", json={"title": "Test Session"})
        assert response.status_code == 200

        session_data = response.json()
        session_id = session_data["id"]
        assert session_data["title"] == "Test Session"

        # Get session
        response = await client.get(f"/session/{session_id}")
        assert response.status_code == 200

        retrieved = response.json()
        assert retrieved["id"] == session_id
        assert retrieved["title"] == "Test Session"


@pytest.mark.asyncio
async def test_list_sessions():
    """Test session listing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create multiple sessions
        await client.post("/session", json={"title": "Session 1"})
        await client.post("/session", json={"title": "Session 2"})

        # List sessions
        response = await client.get("/session")
        assert response.status_code == 200

        sessions = response.json()
        assert len(sessions) >= 2


@pytest.mark.asyncio
async def test_update_session():
    """Test session update."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create session
        response = await client.post("/session", json={"title": "Original"})
        session_id = response.json()["id"]

        # Update session
        response = await client.patch(
            f"/session/{session_id}",
            json={"title": "Updated"}
        )
        assert response.status_code == 200

        updated = response.json()
        assert updated["title"] == "Updated"


@pytest.mark.asyncio
async def test_delete_session():
    """Test session deletion."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create session
        response = await client.post("/session", json={"title": "To Delete"})
        session_id = response.json()["id"]

        # Delete session
        response = await client.delete(f"/session/{session_id}")
        assert response.status_code == 200
        assert response.json() is True

        # Verify it's deleted
        response = await client.get(f"/session/{session_id}")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_messages():
    """Test listing messages in a session."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create session
        response = await client.post("/session", json={"title": "Test"})
        session_id = response.json()["id"]

        # List messages (should be empty)
        response = await client.get(f"/session/{session_id}/message")
        assert response.status_code == 200
        assert response.json() == []
