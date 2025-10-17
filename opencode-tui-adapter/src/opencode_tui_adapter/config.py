"""Configuration management for OpenCode TUI Adapter."""

from pathlib import Path
from typing import Dict, List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


class AgentConfig(BaseSettings):
    """Configuration for an agent."""

    name: str
    description: str
    sdk_type: str = "claude"
    model: str = "claude-3-5-sonnet-20241022"


class ModelConfig(BaseSettings):
    """Configuration for an AI model."""

    id: str
    name: str


class ProviderConfig(BaseSettings):
    """Configuration for an AI provider."""

    id: str
    name: str
    models: Dict[str, ModelConfig] = Field(default_factory=dict)


class ProjectConfig(BaseSettings):
    """Configuration for the project."""

    id: str = "default_project"
    worktree: str = str(Path.home() / "opencode-workspace")
    vcs: str = "git"
    initialized: bool = True


class ServerConfig(BaseSettings):
    """Main server configuration."""

    model_config = SettingsConfigDict(
        env_prefix="OPENCODE_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Server settings
    host: str = "127.0.0.1"
    port: int = 3000
    log_level: str = "INFO"

    # Paths
    state_path: str = str(Path.home() / ".opencode" / "state")
    config_path: str = str(Path.home() / ".opencode" / "config")

    # Project
    project: ProjectConfig = Field(default_factory=ProjectConfig)

    # Agents
    agents: List[AgentConfig] = Field(default_factory=lambda: [
        AgentConfig(
            name="build",
            description="Building agent for development tasks",
            sdk_type="claude",
            model="claude-3-5-sonnet-20241022"
        )
    ])

    # Providers
    providers: List[ProviderConfig] = Field(default_factory=lambda: [
        ProviderConfig(
            id="anthropic",
            name="Anthropic",
            models={
                "claude-3-5-sonnet-20241022": ModelConfig(
                    id="claude-3-5-sonnet-20241022",
                    name="Claude 3.5 Sonnet"
                )
            }
        )
    ])

    # Theme
    theme: str = "system"

    # API Keys (from environment)
    anthropic_api_key: Optional[str] = None

    @classmethod
    def load_from_yaml(cls, path: Path) -> "ServerConfig":
        """Load configuration from YAML file."""
        if not path.exists():
            return cls()

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        return cls(**data)


# Global configuration instance
config = ServerConfig()


def get_config() -> ServerConfig:
    """Get the global configuration instance."""
    return config
