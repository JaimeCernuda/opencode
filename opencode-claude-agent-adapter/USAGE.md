# OpenCode Claude Agent Adapter - Usage Guide

## Overview

This adapter creates a bridge between OpenCode TUI and Claude's Agent SDK, enabling you to chat with Claude directly through the OpenCode terminal interface.

## Architecture

```
┌─────────────────┐
│  OpenCode TUI   │  (Go-based terminal UI)
└────────┬────────┘
         │ HTTP/REST + SSE
         ▼
┌─────────────────┐
│  FastAPI Server │  (This adapter)
│  ├─ Storage     │  (Session/Message management)
│  ├─ Agent Mgr   │  (Claude SDK integration)
│  └─ SSE Stream  │  (Real-time updates)
└────────┬────────┘
         │ Claude SDK
         ▼
┌─────────────────┐
│  Claude API     │  (Anthropic's API)
└─────────────────┘
```

## Installation

### 1. Prerequisites

- Python 3.11 or higher
- `uv` package manager (recommended) or `pip`
- Anthropic API key

### 2. Install Dependencies

Using `uv` (recommended):

```bash
cd opencode-claude-agent-adapter
uv pip install -e .
```

Using `pip`:

```bash
cd opencode-claude-agent-adapter
pip install -e .
```

### 3. Configure Environment

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
CLAUDE_MODEL=claude-opus-4-20250514
OPENCODE_PORT=3000
OPENCODE_HOST=127.0.0.1
```

## Running the Server

### Option 1: Using the run script

```bash
./run.sh
```

### Option 2: Direct Python execution

```bash
uv run python src/opencode_claude_agent/server.py
```

### Option 3: Using the installed command

```bash
opencode-claude-agent
```

The server will start on `http://127.0.0.1:3000` by default.

## Connecting OpenCode TUI

Once the server is running, connect the OpenCode TUI in a separate terminal:

### Linux/Mac

```bash
export OPENCODE_SERVER=http://localhost:3000
./tui
```

### Windows PowerShell

```powershell
$env:OPENCODE_SERVER="http://localhost:3000"
.\tui.exe
```

### Windows CMD

```cmd
set OPENCODE_SERVER=http://localhost:3000
tui.exe
```

## Features

### Session Management

- Create new chat sessions
- List all sessions
- Delete sessions
- Sessions persist during server runtime

### Message Streaming

- Real-time streaming responses from Claude
- Server-Sent Events (SSE) for live updates
- Abort/cancel ongoing requests

### Agent Integration

- Uses Claude Agent SDK for conversation management
- Maintains conversation context per session
- Streaming text responses

## API Endpoints

The adapter implements the OpenCode TUI API specification:

### Core Endpoints

- `GET /project/current` - Get current project information
- `GET /agent` - List available agents
- `POST /session` - Create new session
- `GET /session` - List all sessions
- `GET /session/{id}` - Get session details
- `POST /session/{id}/message` - Send message to Claude
- `POST /session/{id}/abort` - Cancel ongoing request
- `DELETE /session/{id}` - Delete session
- `GET /event` - SSE event stream

### Configuration Endpoints

- `GET /config` - Get configuration
- `GET /config/providers` - List model providers
- `GET /path` - Get filesystem paths

## Troubleshooting

### Server won't start

1. Check if `.env` file exists and contains valid `ANTHROPIC_API_KEY`
2. Ensure port 3000 is not in use: `lsof -i :3000` (Linux/Mac)
3. Check Python version: `python --version` (should be 3.11+)

### TUI can't connect

1. Verify server is running and listening on correct port
2. Check `OPENCODE_SERVER` environment variable is set correctly
3. Look for connection errors in server logs

### No responses from Claude

1. Verify API key is valid
2. Check server logs for error messages
3. Ensure you have API credits/quota available
4. Check network connectivity

### Streaming not working

1. Verify SSE connection in server logs ("SSE client connected")
2. Check browser/client supports Server-Sent Events
3. Look for firewall/proxy issues

## Development

### Project Structure

```
opencode-claude-agent-adapter/
├── src/
│   └── opencode_claude_agent/
│       ├── __init__.py       # Package init
│       ├── server.py         # FastAPI server
│       ├── agent.py          # Claude Agent SDK integration
│       ├── storage.py        # Session/message storage
│       └── models.py         # Pydantic data models
├── pyproject.toml            # Project configuration
├── .env.example              # Environment template
├── .env                      # Your configuration (git-ignored)
├── run.sh                    # Quick start script
└── README.md                 # Project overview
```

### Extending the Adapter

#### Adding Custom Tools

Edit `agent.py` to add custom tools for Claude:

```python
# In ClaudeAgentManager class
def get_tools(self):
    return [
        {
            "name": "custom_tool",
            "description": "Your tool description",
            # ... tool definition
        }
    ]
```

#### Persistent Storage

Currently uses in-memory storage. To add persistence:

1. Modify `storage.py` to use a database (SQLite, PostgreSQL, etc.)
2. Implement save/load methods for sessions and messages
3. Update `lifespan` in `server.py` to load sessions on startup

#### Adding MCP Servers

Integrate Model Context Protocol servers:

1. Install MCP server packages
2. Configure in `.env`
3. Initialize in `agent.py`
4. Pass to Claude SDK when creating conversations

## Performance Tuning

### Response Speed

- Use faster models: `claude-sonnet-4-20250514` instead of opus
- Reduce `CLAUDE_MAX_TOKENS` for shorter responses
- Enable caching for repeated contexts

### Memory Usage

- Implement message history limits per session
- Add session cleanup after inactivity
- Use database storage instead of in-memory

### Concurrent Users

- FastAPI handles multiple connections automatically
- Consider adding rate limiting for production use
- Monitor memory usage with many active sessions

## Security Considerations

### API Key Protection

- Never commit `.env` file to version control
- Use environment variables in production
- Rotate API keys regularly

### Network Security

- Use HTTPS in production (add TLS termination)
- Implement authentication/authorization if needed
- Restrict CORS origins in production

### Input Validation

- All inputs are validated via Pydantic models
- Consider adding rate limiting
- Sanitize file paths if implementing file operations

## Next Steps

1. Test the integration with OpenCode TUI
2. Add support for tools and function calling
3. Implement MCP server integration
4. Add persistent storage (database)
5. Implement user authentication
6. Add comprehensive error handling
7. Write unit tests
8. Add Docker support

## Support

For issues or questions:

- Check the logs in the server terminal
- Review OpenCode TUI documentation
- Refer to Claude Agent SDK documentation at https://github.com/anthropics/claude-agent-sdk-python
- File issues in the project repository
