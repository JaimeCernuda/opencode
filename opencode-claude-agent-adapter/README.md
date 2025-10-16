# OpenCode Claude Agent Adapter

A bridge server that connects OpenCode TUI with Claude's Agent SDK, enabling full agentic capabilities.

## Architecture

```
OpenCode TUI → FastAPI Server → Claude Agent SDK → Claude API
                     ↓
                 SSE Stream ← Real-time responses
```

## Features

- Full OpenCode TUI API implementation
- Claude Agent SDK integration for agentic conversations
- Server-Sent Events (SSE) for real-time streaming
- Session management and persistence
- Support for tools and MCP servers

## Quick Start

### 1. Set up environment

```bash
cd opencode-claude-agent-adapter
```

### 2. Install dependencies

```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

### 3. Start the server

```bash
# Simple start (make sure ANTHROPIC_API_KEY is set)
python src/opencode_claude_agent/server.py

# Or with uv
uv run python src/opencode_claude_agent/server.py

# Or if installed
opencode-claude-agent
```

The server will start on `http://localhost:3000`

### 4. Connect OpenCode TUI

In a separate terminal:

```bash
# Windows PowerShell
$env:OPENCODE_SERVER="http://localhost:3000"
./tui.exe

# Linux/Mac
OPENCODE_SERVER=http://localhost:3000 ./tui
```


## Development

The adapter implements the following key components:

- **FastAPI Server**: REST API endpoints matching OpenCode TUI protocol
- **Agent Manager**: Manages Claude Agent SDK sessions
- **SSE Streaming**: Real-time event streaming to TUI
- **Session Storage**: In-memory session and message storage

## Endpoints

See the OpenCode documentation for full API specification. Key endpoints:

- `GET /project/current` - Get current project info
- `POST /session` - Create new session
- `POST /session/{id}/message` - Send message to agent
- `GET /event` - SSE event stream
- `POST /session/{id}/abort` - Cancel running request

## How It Works

1. **TUI sends message** → POST `/session/{id}/message`
2. **Server receives** → Creates Claude Agent SDK conversation
3. **Agent processes** → Streams responses via SSE
4. **TUI displays** → Real-time updates in terminal

## License

MIT
