# OpenCode TUI Adapter

Backend adapter server that connects the OpenCode TUI (Terminal User Interface) to the Claude Agent SDK, enabling AI-powered coding assistance through a terminal interface.

## Overview

This project implements a FastAPI-based server that:
- Exposes REST API endpoints compatible with the OpenCode TUI
- Integrates with the Claude Agent SDK for Python
- Manages conversation sessions with context retention
- Provides real-time updates via Server-Sent Events (SSE)
- Supports multiple AI agents and providers

## Architecture

```
┌─────────────────────┐
│  OpenCode TUI (Go)  │
│  - User Interface   │
└──────────┬──────────┘
           │ HTTP/REST + SSE
           ▼
┌─────────────────────┐
│  Backend Server     │
│  (FastAPI/Python)   │
│  - Session Mgmt     │
│  - Event Bus        │
│  - Translation      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Claude Agent SDK   │
│  (Python Library)   │
└─────────────────────┘
```

## Features

### Phase 1: Core Communication Infrastructure ✅

- **Session Management**
  - Create, retrieve, update, and delete sessions
  - Session state persistence
  - Parent-child session relationships

- **Message Exchange**
  - Send prompts to Claude
  - Receive streaming responses
  - Message history tracking
  - Format translation (SDK ↔ TUI)

- **Real-Time Events**
  - Server-Sent Events (SSE) streaming
  - Event broadcasting to multiple clients
  - Keep-alive mechanism

- **Configuration**
  - Project and agent configuration
  - Provider/model management
  - Filesystem path handling

- **Logging**
  - Structured JSON logging
  - Request/response logging
  - Debug and error tracking

## Installation

### Prerequisites

- Python 3.13 or higher
- Claude Code CLI (`npm install -g @anthropic-ai/claude-code`)
- uv package manager

### Setup

```bash
# Clone the repository
cd opencode-tui-adapter

# Install dependencies
uv sync

# Install dev dependencies (for testing)
uv sync --extra dev

# Set up environment variables
export ANTHROPIC_API_KEY="your-api-key"
export OPENCODE_SERVER_HOST="127.0.0.1"
export OPENCODE_SERVER_PORT="3000"
```

## Usage

### Running the Server

```bash
# Run with uv
uv run opencode-tui-adapter

# Or with Python directly
uv run python -m opencode_tui_adapter.server
```

The server will start on `http://127.0.0.1:3000` by default.

### Configuration

Configuration can be set via:
1. Environment variables (prefix: `OPENCODE_`)
2. `.env` file
3. Code defaults

Example `.env`:
```bash
OPENCODE_HOST=127.0.0.1
OPENCODE_PORT=3000
OPENCODE_LOG_LEVEL=INFO
ANTHROPIC_API_KEY=sk-ant-...
```

### Debug Logging

The adapter includes comprehensive debug logging for full system tracing:

```bash
# Enable debug logging
export OPENCODE_LOG_LEVEL=DEBUG
uv run opencode-tui-adapter
```

Debug logging provides:
- ✅ Function entry/exit with inputs and outputs
- ✅ Internal state changes (session creation, SDK operations, etc.)
- ✅ Message translation steps
- ✅ Event broadcasting tracking
- ✅ Structured JSON output for easy parsing

For complete documentation, see [DEBUG_LOGGING.md](./DEBUG_LOGGING.md).

**Example debug output:**
```bash
# View debug logs with jq
OPENCODE_LOG_LEVEL=DEBUG uv run opencode-tui-adapter 2>&1 | jq 'select(.event | contains("function"))'

# Track a specific session
OPENCODE_LOG_LEVEL=DEBUG uv run opencode-tui-adapter 2>&1 | jq 'select(.session_id == "session_abc123")'
```

### API Endpoints

#### Core Endpoints

- `GET /project/current` - Get current project info
- `GET /agent` - List available agents
- `GET /path` - Get filesystem paths
- `GET /config` - Get configuration
- `GET /config/providers` - List AI providers and models

#### Session Endpoints

- `POST /session` - Create new session
- `GET /session` - List all sessions
- `GET /session/{id}` - Get specific session
- `PATCH /session/{id}` - Update session
- `DELETE /session/{id}` - Delete session
- `POST /session/{id}/abort` - Cancel operation

#### Message Endpoints

- `GET /session/{id}/message` - List messages
- `POST /session/{id}/message` - Send message

#### Events

- `GET /event` - SSE stream for real-time updates

## Testing

### Run All Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ -v --cov=src/opencode_tui_adapter --cov-report=term-missing

# Run specific test suite
uv run pytest tests/unit -v
uv run pytest tests/integration -v
```

### Test Coverage

Current coverage: **75%**

```
Total                                              446    110    75%
```

### Test Structure

```
tests/
├── unit/
│   ├── test_session_manager.py   # Session lifecycle tests
│   ├── test_event_bus.py          # Event broadcasting tests
│   └── test_translation.py        # Message format translation tests
└── integration/
    └── test_api_endpoints.py      # End-to-end API tests
```

## Development

### Project Structure

```
src/opencode_tui_adapter/
├── __init__.py
├── server.py              # Main FastAPI application
├── config.py              # Configuration management
├── session/
│   ├── models.py          # Session data models
│   └── manager.py         # Session lifecycle
├── events/
│   ├── models.py          # Event data models
│   └── bus.py             # SSE event broadcasting
├── logging/
│   └── config.py          # Structured logging setup
└── utils/
    ├── id_generator.py    # ID generation utilities
    └── translation.py     # Message format conversion
```

### Code Quality

```bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

## Implementation Status

### ✅ Phase 1: Core Communication Infrastructure (Complete)
- Session management
- Message exchange
- SSE event streaming
- Configuration endpoints
- Comprehensive tests (24 tests, all passing)

### 🚧 Phase 2: UI Operations (Planned)
- Theme switching
- Advanced configuration
- UI state management

### 📋 Phase 3: Extended Functionality (Planned)
- Advanced session operations (fork, share, revert)
- Permission handling
- File operations
- Search operations
- Tool management

## Documentation

- [Implementation Analysis](../opencode-claude-adapter/IMPLEMENTATION_ANALYSIS.md) - Comprehensive analysis of TUI-SDK integration
- [Technical Implementation Plan](../opencode-claude-adapter/IMPLEMENTATION_PLAN.md) - Detailed implementation roadmap
- [OpenCode Endpoints](../opencode-claude-adapter/OPENCODE_ENDPOINTS.md) - API specification
- [TUI Architecture](../opencode-claude-adapter/TUI_ARCHITECTURE.md) - TUI design overview
- [Claude SDK Documentation](../opencode-claude-adapter/CLAUDE_AGENT_SDK_PYTHON.md) - SDK reference

## Troubleshooting

### Common Issues

**1. Session creation fails with "Working directory does not exist"**

Solution: Ensure the workspace directory exists:
```bash
mkdir -p ~/opencode-workspace
```

Or set a custom directory via environment:
```bash
export OPENCODE_PROJECT__WORKTREE=/path/to/your/project
```

**2. Claude SDK not found**

Solution: Install Claude Code CLI:
```bash
npm install -g @anthropic-ai/claude-code
```

**3. Port already in use**

Solution: Change the port:
```bash
export OPENCODE_PORT=3001
```

## Contributing

This project follows the coding standards documented in the main OpenCode repository:

- Keep code in single functions unless composable/reusable
- DO NOT unnecessarily destructure variables
- DO NOT use `else` statements unless necessary
- PREFER single-word variable names where possible
- Use async/await for asynchronous operations
- Write comprehensive tests for new features

---

**Status**: Phase 1 Complete ✅
**Test Coverage**: 75% (24/24 tests passing)
**Next**: Phase 2 - UI Operations
