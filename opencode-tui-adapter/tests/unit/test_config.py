"""Unit tests for configuration management."""

import pytest
from pathlib import Path
import tempfile
import yaml

from opencode_tui_adapter.config import ServerConfig


def test_config_update_theme():
    """Test theme update functionality."""
    config = ServerConfig()

    # Initial theme
    assert config.theme == "system"

    # Update to valid theme
    config.update_theme("dark")
    assert config.theme == "dark"

    # Update to another valid theme
    config.update_theme("light")
    assert config.theme == "light"

    # Invalid theme should raise error
    with pytest.raises(ValueError, match="Invalid theme"):
        config.update_theme("invalid")


def test_config_update_from_dict():
    """Test configuration update from dictionary."""
    config = ServerConfig()

    # Update theme
    config.update_from_dict({"theme": "dark"})
    assert config.theme == "dark"

    # Update log level
    config.update_from_dict({"log_level": "DEBUG"})
    assert config.log_level == "DEBUG"

    # Update multiple fields
    config.update_from_dict({
        "theme": "light",
        "log_level": "WARNING"
    })
    assert config.theme == "light"
    assert config.log_level == "WARNING"

    # Unknown fields should be ignored
    config.update_from_dict({"unknown_field": "value"})
    assert not hasattr(config, "unknown_field")

    # Invalid theme should raise error
    with pytest.raises(ValueError, match="Invalid theme"):
        config.update_from_dict({"theme": "invalid"})

    # Invalid log level should raise error
    with pytest.raises(ValueError, match="Invalid log_level"):
        config.update_from_dict({"log_level": "INVALID"})


def test_config_save_to_yaml():
    """Test saving configuration to YAML file."""
    config = ServerConfig()
    config.theme = "dark"
    config.log_level = "DEBUG"

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.yaml"

        # Save config
        config.save_to_yaml(config_path)

        # Verify file exists
        assert config_path.exists()

        # Verify content
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        assert data["theme"] == "dark"
        assert data["log_level"] == "DEBUG"
        assert "anthropic_api_key" not in data  # Should not save sensitive data


def test_config_load_from_yaml():
    """Test loading configuration from YAML file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.yaml"

        # Create test config file
        test_data = {
            "theme": "dark",
            "log_level": "DEBUG",
            "host": "0.0.0.0",
            "port": 8000,
        }

        with open(config_path, "w") as f:
            yaml.dump(test_data, f)

        # Load config
        config = ServerConfig.load_from_yaml(config_path)

        assert config.theme == "dark"
        assert config.log_level == "DEBUG"
        assert config.host == "0.0.0.0"
        assert config.port == 8000


def test_config_load_from_nonexistent_yaml():
    """Test loading from non-existent file returns default config."""
    config = ServerConfig.load_from_yaml(Path("/nonexistent/path.yaml"))

    # Should return default config
    assert config.theme == "system"
    assert config.log_level == "INFO"
    assert config.host == "127.0.0.1"
    assert config.port == 3000


def test_config_persistence_roundtrip():
    """Test saving and loading configuration maintains values."""
    config1 = ServerConfig()
    config1.theme = "dark"
    config1.log_level = "DEBUG"

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"

        # Save
        config1.save_to_yaml(config_path)

        # Load
        config2 = ServerConfig.load_from_yaml(config_path)

        # Verify values match
        assert config2.theme == config1.theme
        assert config2.log_level == config1.log_level
        assert config2.host == config1.host
        assert config2.port == config1.port
