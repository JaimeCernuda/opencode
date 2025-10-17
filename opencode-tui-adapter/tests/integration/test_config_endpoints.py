"""Integration tests for configuration endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from opencode_tui_adapter.server import app


@pytest.mark.asyncio
async def test_get_config():
    """Test GET /config endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/config")

        assert response.status_code == 200
        data = response.json()

        # Verify required fields
        assert "theme" in data
        assert "share" in data
        assert "model" in data
        assert "keybinds" in data
        assert "tui" in data


@pytest.mark.asyncio
async def test_patch_config_theme():
    """Test PATCH /config to update theme."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Update theme to dark
        response = await client.patch("/config", json={"theme": "dark"})

        assert response.status_code == 200
        data = response.json()
        assert data["theme"] == "dark"

        # Verify GET returns updated value
        response = await client.get("/config")
        assert response.status_code == 200
        assert response.json()["theme"] == "dark"

        # Update theme to light
        response = await client.patch("/config", json={"theme": "light"})
        assert response.status_code == 200
        assert response.json()["theme"] == "light"

        # Reset to system
        await client.patch("/config", json={"theme": "system"})


@pytest.mark.asyncio
async def test_patch_config_log_level():
    """Test PATCH /config to update log level."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Update log level
        response = await client.patch("/config", json={"log_level": "DEBUG"})

        assert response.status_code == 200

        # Note: Log level doesn't appear in response, but config should be updated
        # This is expected as log_level is internal server config

        # Reset to INFO
        await client.patch("/config", json={"log_level": "INFO"})


@pytest.mark.asyncio
async def test_patch_config_multiple_fields():
    """Test PATCH /config with multiple fields."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch("/config", json={
            "theme": "dark",
            "log_level": "DEBUG"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["theme"] == "dark"

        # Reset
        await client.patch("/config", json={"theme": "system", "log_level": "INFO"})


@pytest.mark.asyncio
async def test_patch_config_invalid_theme():
    """Test PATCH /config with invalid theme."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch("/config", json={"theme": "invalid"})

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "Invalid theme" in data["error"]


@pytest.mark.asyncio
async def test_patch_config_invalid_log_level():
    """Test PATCH /config with invalid log level."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch("/config", json={"log_level": "INVALID"})

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "Invalid log_level" in data["error"]


@pytest.mark.asyncio
async def test_patch_config_unknown_fields_ignored():
    """Test that unknown fields in PATCH /config are ignored."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Should not fail, just ignore unknown field
        response = await client.patch("/config", json={
            "theme": "dark",
            "unknown_field": "value"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["theme"] == "dark"
        assert "unknown_field" not in data

        # Reset
        await client.patch("/config", json={"theme": "system"})
