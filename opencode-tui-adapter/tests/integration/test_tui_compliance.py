"""
Comprehensive TUI compliance tests.
Validates that every response field matches the exact structure expected by the TUI
as documented in OPENCODE_ENDPOINTS.md.
"""

import asyncio
import json
import subprocess

import httpx
import pytest


SERVER_URL = "http://127.0.0.1:3002"  # Use different port


class DeployedServer:
    """Context manager for deploying the server during tests."""

    def __init__(self, port: int = 3002):
        self.port = port
        self.process = None

    async def __aenter__(self):
        """Start the server."""
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
                "error",
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


def validate_project_schema(data: dict):
    """Validate project response against TUI schema."""
    required_fields = ["id", "worktree", "vcs", "initialized"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    assert isinstance(data["id"], str), "id must be string"
    assert isinstance(data["worktree"], str), "worktree must be string"
    assert data["vcs"] in ["git", "none"], "vcs must be 'git' or 'none'"
    assert isinstance(data["initialized"], bool), "initialized must be boolean"


def validate_agent_schema(agent: dict):
    """Validate agent response against TUI schema."""
    required_fields = ["name", "description", "mode", "model"]
    for field in required_fields:
        assert field in agent, f"Missing required field: {field}"

    assert isinstance(agent["name"], str)
    assert isinstance(agent["description"], str)
    assert agent["mode"] in ["primary", "subagent", "all"]

    # Validate model structure
    model = agent["model"]
    assert "providerID" in model
    assert "modelID" in model
    assert isinstance(model["providerID"], str)
    assert isinstance(model["modelID"], str)


def validate_session_schema(session: dict):
    """Validate session response against TUI schema."""
    required_fields = ["id", "projectID", "directory", "title", "version", "time"]
    for field in required_fields:
        assert field in session, f"Missing required field: {field}"

    assert isinstance(session["id"], str)
    assert isinstance(session["projectID"], str)
    assert isinstance(session["directory"], str)
    assert isinstance(session["title"], str)
    assert isinstance(session["version"], str)

    # Validate time structure
    time_data = session["time"]
    assert "created" in time_data
    assert "updated" in time_data
    assert isinstance(time_data["created"], int)
    assert isinstance(time_data["updated"], int)
    assert time_data["created"] <= time_data["updated"]


def validate_message_schema(message: dict):
    """Validate message response against TUI schema."""
    required_fields = ["info", "parts"]
    for field in required_fields:
        assert field in message, f"Missing required field: {field}"

    # Validate info structure
    info = message["info"]
    assert "id" in info
    assert "sessionID" in info
    assert "role" in info
    assert "time" in info

    assert isinstance(info["id"], str)
    assert isinstance(info["sessionID"], str)
    assert info["role"] in ["user", "assistant"]

    # Validate time structure
    time_data = info["time"]
    assert "created" in time_data
    assert isinstance(time_data["created"], int)

    # Assistant messages should have completed time
    if info["role"] == "assistant" and "completed" in time_data:
        assert isinstance(time_data["completed"], int)
        assert time_data["completed"] >= time_data["created"]

    # Validate parts structure
    parts = message["parts"]
    assert isinstance(parts, list)

    for part in parts:
        assert "id" in part
        assert "type" in part
        assert isinstance(part["id"], str)
        assert isinstance(part["type"], str)


def validate_provider_schema(data: dict):
    """Validate provider response against TUI schema."""
    required_fields = ["providers", "default"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    assert isinstance(data["providers"], list)
    assert isinstance(data["default"], dict)

    for provider in data["providers"]:
        assert "id" in provider
        assert "name" in provider
        assert "models" in provider
        assert isinstance(provider["models"], dict)

        # Each model should have proper structure
        for model_id, model_data in provider["models"].items():
            assert "id" in model_data
            assert "name" in model_data
            assert isinstance(model_data["id"], str)
            assert isinstance(model_data["name"], str)


@pytest.mark.asyncio
async def test_project_current_compliance():
    """Test /project/current complete compliance."""
    async with DeployedServer():
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVER_URL}/project/current")
            assert response.status_code == 200

            data = response.json()
            validate_project_schema(data)

            print(f"✅ /project/current compliant")


@pytest.mark.asyncio
async def test_agent_list_compliance():
    """Test /agent complete compliance."""
    async with DeployedServer():
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVER_URL}/agent")
            assert response.status_code == 200

            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0

            for agent in data:
                validate_agent_schema(agent)

            print(f"✅ /agent compliant ({len(data)} agents)")


@pytest.mark.asyncio
async def test_config_providers_compliance():
    """Test /config/providers complete compliance."""
    async with DeployedServer():
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVER_URL}/config/providers")
            assert response.status_code == 200

            data = response.json()
            validate_provider_schema(data)

            print(f"✅ /config/providers compliant")


@pytest.mark.asyncio
async def test_session_create_compliance():
    """Test POST /session complete compliance."""
    async with DeployedServer():
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SERVER_URL}/session", json={"title": "Compliance Test"}
            )
            assert response.status_code == 200

            data = response.json()
            validate_session_schema(data)

            assert data["title"] == "Compliance Test"

            print(f"✅ POST /session compliant")


@pytest.mark.asyncio
async def test_session_get_compliance():
    """Test GET /session/{id} complete compliance."""
    async with DeployedServer():
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create session
            create_response = await client.post(f"{SERVER_URL}/session")
            session_id = create_response.json()["id"]

            # Get session
            response = await client.get(f"{SERVER_URL}/session/{session_id}")
            assert response.status_code == 200

            data = response.json()
            validate_session_schema(data)

            print(f"✅ GET /session/{{id}} compliant")


@pytest.mark.asyncio
async def test_session_list_compliance():
    """Test GET /session complete compliance."""
    async with DeployedServer():
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create multiple sessions
            await client.post(f"{SERVER_URL}/session", json={"title": "Session 1"})
            await client.post(f"{SERVER_URL}/session", json={"title": "Session 2"})

            # List sessions
            response = await client.get(f"{SERVER_URL}/session")
            assert response.status_code == 200

            data = response.json()
            assert isinstance(data, list)

            for session in data:
                validate_session_schema(session)

            print(f"✅ GET /session compliant ({len(data)} sessions)")


@pytest.mark.asyncio
async def test_message_send_compliance():
    """Test POST /session/{id}/message complete compliance."""
    async with DeployedServer():
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Create session
            create_response = await client.post(f"{SERVER_URL}/session")
            session_id = create_response.json()["id"]

            # Send message in exact TUI format
            message_request = {
                "messageID": "test_compliance",
                "agent": "build",
                "model": {"providerID": "anthropic", "modelID": "claude-3-5-sonnet"},
                "parts": [{"type": "text", "text": "Respond with just 'OK'"}],
            }

            response = await client.post(
                f"{SERVER_URL}/session/{session_id}/message", json=message_request
            )
            assert response.status_code == 200

            data = response.json()
            validate_message_schema(data)

            # Verify response is from assistant
            assert data["info"]["role"] == "assistant"
            assert data["info"]["sessionID"] == session_id

            print(f"✅ POST /session/{{id}}/message compliant")


@pytest.mark.asyncio
async def test_message_list_compliance():
    """Test GET /session/{id}/message complete compliance."""
    async with DeployedServer():
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create session
            create_response = await client.post(f"{SERVER_URL}/session")
            session_id = create_response.json()["id"]

            # List messages
            response = await client.get(f"{SERVER_URL}/session/{session_id}/message")
            assert response.status_code == 200

            data = response.json()
            assert isinstance(data, list)

            # If there are messages, validate them
            for message in data:
                validate_message_schema(message)

            print(f"✅ GET /session/{{id}}/message compliant")


@pytest.mark.asyncio
async def test_all_endpoints_return_json():
    """Verify all endpoints return valid JSON."""
    async with DeployedServer():
        async with httpx.AsyncClient(timeout=30.0) as client:
            endpoints = [
                ("GET", "/project/current"),
                ("GET", "/agent"),
                ("GET", "/path"),
                ("GET", "/config"),
                ("GET", "/config/providers"),
                ("GET", "/command"),
                ("GET", "/mcp"),
            ]

            for method, path in endpoints:
                response = await client.request(method, f"{SERVER_URL}{path}")
                assert response.status_code == 200

                # Should be valid JSON
                data = response.json()
                assert data is not None

                print(f"✅ {method} {path} returns valid JSON")


@pytest.mark.asyncio
async def test_error_responses_format():
    """Test that error responses have proper format."""
    async with DeployedServer():
        async with httpx.AsyncClient() as client:
            # Try to get non-existent session
            response = await client.get(f"{SERVER_URL}/session/nonexistent_id")
            assert response.status_code == 404

            data = response.json()
            assert "error" in data
            assert isinstance(data["error"], str)

            print(f"✅ Error responses properly formatted")


@pytest.mark.asyncio
async def test_complete_tui_workflow_compliance():
    """
    Test that a complete TUI workflow produces spec-compliant responses
    at every step.
    """
    async with DeployedServer():
        async with httpx.AsyncClient(timeout=60.0) as client:
            results = []

            # Step 1: Get project
            response = await client.get(f"{SERVER_URL}/project/current")
            assert response.status_code == 200
            validate_project_schema(response.json())
            results.append("✓ Project info compliant")

            # Step 2: List agents
            response = await client.get(f"{SERVER_URL}/agent")
            assert response.status_code == 200
            for agent in response.json():
                validate_agent_schema(agent)
            results.append("✓ Agent list compliant")

            # Step 3: Get providers
            response = await client.get(f"{SERVER_URL}/config/providers")
            assert response.status_code == 200
            validate_provider_schema(response.json())
            results.append("✓ Providers compliant")

            # Step 4: Create session
            response = await client.post(
                f"{SERVER_URL}/session", json={"title": "Full Workflow"}
            )
            assert response.status_code == 200
            session_data = response.json()
            validate_session_schema(session_data)
            session_id = session_data["id"]
            results.append("✓ Session creation compliant")

            # Step 5: Send message
            message_request = {
                "messageID": "workflow_msg",
                "agent": "build",
                "model": {"providerID": "anthropic", "modelID": "claude-3-5-sonnet"},
                "parts": [{"type": "text", "text": "Say OK"}],
            }
            response = await client.post(
                f"{SERVER_URL}/session/{session_id}/message", json=message_request
            )
            assert response.status_code == 200
            validate_message_schema(response.json())
            results.append("✓ Message send compliant")

            # Step 6: List messages
            response = await client.get(f"{SERVER_URL}/session/{session_id}/message")
            assert response.status_code == 200
            for message in response.json():
                validate_message_schema(message)
            results.append("✓ Message list compliant")

            # Step 7: Update session
            response = await client.patch(
                f"{SERVER_URL}/session/{session_id}",
                json={"title": "Updated Workflow"},
            )
            assert response.status_code == 200
            validate_session_schema(response.json())
            results.append("✓ Session update compliant")

            # Step 8: List sessions
            response = await client.get(f"{SERVER_URL}/session")
            assert response.status_code == 200
            for session in response.json():
                validate_session_schema(session)
            results.append("✓ Session list compliant")

            # Step 9: Delete session
            response = await client.delete(f"{SERVER_URL}/session/{session_id}")
            assert response.status_code == 200
            assert response.json() is True
            results.append("✓ Session deletion compliant")

            # Print results
            print("\n" + "=" * 60)
            print("COMPLETE TUI WORKFLOW COMPLIANCE TEST")
            print("=" * 60)
            for result in results:
                print(result)
            print("=" * 60)
            print("✅ ALL STEPS COMPLIANT WITH TUI SPECIFICATION")
            print("=" * 60)
