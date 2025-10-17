"""
Integration tests that actually deploy the server and test it via HTTP.
These tests validate that responses match the TUI's expectations.
"""

import asyncio
import json
import subprocess
import time
from typing import AsyncIterator

import httpx
import pytest
from httpx_sse import aconnect_sse


SERVER_URL = "http://127.0.0.1:3001"  # Use different port for testing


class DeployedServer:
    """Context manager for deploying the server during tests."""

    def __init__(self, port: int = 3001):
        self.port = port
        self.process = None

    async def __aenter__(self):
        """Start the server."""
        # Start server as subprocess
        self.process = subprocess.Popen(
            [
                "uv",
                "run",
                "uvicorn",
                "opencode_tui_adapter.server:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
                "--log-level",
                "warning",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to be ready
        await self._wait_for_server()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Stop the server."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

    async def _wait_for_server(self, max_attempts: int = 30):
        """Wait for server to be ready."""
        for i in range(max_attempts):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"http://127.0.0.1:{self.port}/config")
                    if response.status_code == 200:
                        return
            except (httpx.ConnectError, httpx.RemoteProtocolError):
                await asyncio.sleep(0.5)

        raise TimeoutError(f"Server did not start within {max_attempts * 0.5} seconds")


@pytest.mark.asyncio
async def test_server_startup_and_health():
    """Test that the server starts and responds to requests."""
    async with DeployedServer():
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVER_URL}/config")
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_project_current_format():
    """Validate /project/current response matches TUI expectations."""
    async with DeployedServer():
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVER_URL}/project/current")

            assert response.status_code == 200
            data = response.json()

            # Validate required fields per OPENCODE_ENDPOINTS.md
            assert "id" in data
            assert "worktree" in data
            assert "vcs" in data
            assert "initialized" in data

            assert isinstance(data["id"], str)
            assert isinstance(data["worktree"], str)
            assert data["vcs"] in ["git", "none"]
            assert isinstance(data["initialized"], bool)


@pytest.mark.asyncio
async def test_agent_list_format():
    """Validate /agent response matches TUI expectations."""
    async with DeployedServer():
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVER_URL}/agent")

            assert response.status_code == 200
            data = response.json()

            # Should be an array
            assert isinstance(data, list)
            assert len(data) > 0

            # Validate first agent structure
            agent = data[0]
            assert "name" in agent
            assert "description" in agent
            assert "mode" in agent
            assert "model" in agent

            # Validate model structure
            model = agent["model"]
            assert "providerID" in model
            assert "modelID" in model


@pytest.mark.asyncio
async def test_config_providers_format():
    """Validate /config/providers response matches TUI expectations."""
    async with DeployedServer():
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVER_URL}/config/providers")

            assert response.status_code == 200
            data = response.json()

            # Required top-level fields
            assert "providers" in data
            assert "default" in data

            # Validate providers structure
            assert isinstance(data["providers"], list)
            provider = data["providers"][0]
            assert "id" in provider
            assert "name" in provider
            assert "models" in provider

            # Validate models structure
            models = provider["models"]
            assert isinstance(models, dict)

            # Validate default structure
            assert isinstance(data["default"], dict)


@pytest.mark.asyncio
async def test_session_creation_format():
    """Validate POST /session response matches TUI expectations."""
    async with DeployedServer():
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create session
            response = await client.post(
                f"{SERVER_URL}/session", json={"title": "Test Session"}
            )

            assert response.status_code == 200
            data = response.json()

            # Validate session structure per OPENCODE_ENDPOINTS.md
            assert "id" in data
            assert "projectID" in data
            assert "directory" in data
            assert "title" in data
            assert "version" in data
            assert "time" in data

            # Validate time structure
            time_data = data["time"]
            assert "created" in time_data
            assert "updated" in time_data
            assert isinstance(time_data["created"], int)
            assert isinstance(time_data["updated"], int)

            # Validate title
            assert data["title"] == "Test Session"


@pytest.mark.asyncio
async def test_session_list_format():
    """Validate GET /session response matches TUI expectations."""
    async with DeployedServer():
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create a session first
            create_response = await client.post(
                f"{SERVER_URL}/session", json={"title": "Test Session"}
            )
            assert create_response.status_code == 200

            # List sessions
            response = await client.get(f"{SERVER_URL}/session")

            assert response.status_code == 200
            data = response.json()

            # Should be an array
            assert isinstance(data, list)
            assert len(data) > 0

            # Validate first session has proper structure
            session = data[0]
            assert "id" in session
            assert "projectID" in session
            assert "title" in session
            assert "time" in session


@pytest.mark.asyncio
async def test_session_get_format():
    """Validate GET /session/{id} response matches TUI expectations."""
    async with DeployedServer():
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create session
            create_response = await client.post(
                f"{SERVER_URL}/session", json={"title": "Get Test"}
            )
            session_id = create_response.json()["id"]

            # Get session
            response = await client.get(f"{SERVER_URL}/session/{session_id}")

            assert response.status_code == 200
            data = response.json()

            assert data["id"] == session_id
            assert data["title"] == "Get Test"


@pytest.mark.asyncio
async def test_session_update_format():
    """Validate PATCH /session/{id} response matches TUI expectations."""
    async with DeployedServer():
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create session
            create_response = await client.post(f"{SERVER_URL}/session")
            session_id = create_response.json()["id"]

            # Update session
            response = await client.patch(
                f"{SERVER_URL}/session/{session_id}", json={"title": "Updated Title"}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["id"] == session_id
            assert data["title"] == "Updated Title"
            assert data["time"]["updated"] >= data["time"]["created"]


@pytest.mark.asyncio
async def test_session_delete():
    """Validate DELETE /session/{id} response."""
    async with DeployedServer():
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create session
            create_response = await client.post(f"{SERVER_URL}/session")
            session_id = create_response.json()["id"]

            # Delete session
            response = await client.delete(f"{SERVER_URL}/session/{session_id}")

            assert response.status_code == 200
            assert response.json() is True

            # Verify it's deleted
            get_response = await client.get(f"{SERVER_URL}/session/{session_id}")
            assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_messages_list_format():
    """Validate GET /session/{id}/message response format."""
    async with DeployedServer():
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create session
            create_response = await client.post(f"{SERVER_URL}/session")
            session_id = create_response.json()["id"]

            # List messages (should be empty)
            response = await client.get(f"{SERVER_URL}/session/{session_id}/message")

            assert response.status_code == 200
            data = response.json()

            # Should be an array (empty initially)
            assert isinstance(data, list)


@pytest.mark.asyncio
async def test_message_send_format():
    """Validate POST /session/{id}/message response matches TUI expectations."""
    async with DeployedServer():
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Create session
            create_response = await client.post(f"{SERVER_URL}/session")
            session_id = create_response.json()["id"]

            # Send message in TUI format
            message_request = {
                "messageID": "test_msg_123",
                "agent": "build",
                "model": {"providerID": "anthropic", "modelID": "claude-3-5-sonnet"},
                "parts": [{"type": "text", "text": "Say hello in one word"}],
            }

            response = await client.post(
                f"{SERVER_URL}/session/{session_id}/message", json=message_request
            )

            assert response.status_code == 200
            data = response.json()

            # Validate message structure per OPENCODE_ENDPOINTS.md
            assert "info" in data
            assert "parts" in data

            # Validate info structure
            info = data["info"]
            assert "id" in info
            assert "sessionID" in info
            assert "role" in info
            assert "time" in info

            assert info["sessionID"] == session_id
            assert info["role"] == "assistant"

            # Validate time structure
            time_data = info["time"]
            assert "created" in time_data
            assert "completed" in time_data

            # Validate parts structure
            parts = data["parts"]
            assert isinstance(parts, list)
            assert len(parts) > 0

            # Each part should have proper structure
            for part in parts:
                assert "id" in part
                assert "type" in part


@pytest.mark.asyncio
async def test_sse_stream_format():
    """Validate /event SSE stream matches TUI expectations."""
    async with DeployedServer():
        events_received = []

        async with httpx.AsyncClient(timeout=10.0) as client:
            async with aconnect_sse(
                client, "GET", f"{SERVER_URL}/event"
            ) as event_source:
                # Collect first event
                async for sse in event_source.aiter_sse():
                    event_data = json.loads(sse.data)
                    events_received.append(event_data)

                    # Break after first event
                    if len(events_received) >= 1:
                        break

        # Should receive server.connected event
        assert len(events_received) > 0
        first_event = events_received[0]

        assert "type" in first_event
        assert "properties" in first_event
        assert first_event["type"] == "server.connected"


@pytest.mark.asyncio
async def test_sse_session_created_event():
    """Validate SSE events are broadcast when session is created."""
    async with DeployedServer():
        events_received = []

        async with httpx.AsyncClient(timeout=30.0) as http_client:
            # Start SSE listener
            async def listen_for_events():
                async with aconnect_sse(
                    http_client, "GET", f"{SERVER_URL}/event"
                ) as event_source:
                    async for sse in event_source.aiter_sse():
                        event_data = json.loads(sse.data)
                        events_received.append(event_data)
                        # Stop after receiving session.updated
                        if event_data.get("type") == "session.updated":
                            break

            # Create tasks for listening and creating session
            listen_task = asyncio.create_task(listen_for_events())

            # Wait a bit for SSE connection
            await asyncio.sleep(1)

            # Create a session (should trigger event)
            await http_client.post(f"{SERVER_URL}/session", json={"title": "Test"})

            # Wait for events
            await asyncio.wait_for(listen_task, timeout=5)

        # Should have received server.connected and session.updated
        event_types = [e["type"] for e in events_received]
        assert "server.connected" in event_types
        assert "session.updated" in event_types

        # Validate session.updated event structure
        session_event = next(e for e in events_received if e["type"] == "session.updated")
        assert "properties" in session_event
        assert "session" in session_event["properties"]


@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """
    Test complete TUI workflow:
    1. Get project info
    2. Create session
    3. Send message
    4. Receive response
    5. List messages
    6. Delete session
    """
    async with DeployedServer():
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 1. Get project info
            project_response = await client.get(f"{SERVER_URL}/project/current")
            assert project_response.status_code == 200
            project = project_response.json()
            print(f"✓ Got project: {project['id']}")

            # 2. Create session
            session_response = await client.post(
                f"{SERVER_URL}/session", json={"title": "E2E Test"}
            )
            assert session_response.status_code == 200
            session = session_response.json()
            session_id = session["id"]
            print(f"✓ Created session: {session_id}")

            # 3. Send message
            message_request = {
                "messageID": "e2e_msg",
                "agent": "build",
                "model": {"providerID": "anthropic", "modelID": "claude-3-5-sonnet"},
                "parts": [{"type": "text", "text": "Say 'hello' in one word"}],
            }
            message_response = await client.post(
                f"{SERVER_URL}/session/{session_id}/message", json=message_request
            )
            assert message_response.status_code == 200
            message_data = message_response.json()
            print(f"✓ Sent message, got {len(message_data['parts'])} parts in response")

            # 4. Verify response structure
            assert message_data["info"]["role"] == "assistant"
            assert len(message_data["parts"]) > 0
            print(f"✓ Response has correct structure")

            # 5. List messages
            messages_response = await client.get(
                f"{SERVER_URL}/session/{session_id}/message"
            )
            assert messages_response.status_code == 200
            messages = messages_response.json()
            print(f"✓ Listed {len(messages)} messages")

            # 6. Delete session
            delete_response = await client.delete(f"{SERVER_URL}/session/{session_id}")
            assert delete_response.status_code == 200
            assert delete_response.json() is True
            print(f"✓ Deleted session")

            print("\n✅ End-to-end workflow complete!")
