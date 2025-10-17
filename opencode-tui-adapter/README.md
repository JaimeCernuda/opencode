# OpenCode TUI Adapter

A logging/testing server that implements the OpenCode TUI API to understand the protocol before building a full CrewAI integration.

## Quick Start

### 1. Start the Logging Server

```bash
cd opencode-tui-adapter
uv run python src/opencode_tui_adapter/server.py
```

The server will start on `http://localhost:3000` and log all incoming requests.

### 2. Connect the OpenCode Go TUI

In a separate terminal:

```bash
# Build the Go TUI (if not already built)
cd ../packages/tui/cmd/opencode
go build -o tui.exe main.go

# Run the TUI pointing to your logging server
export OPENCODE_SERVER=http://localhost:3000
./tui
```

Or on Windows PowerShell:
```powershell
$env:OPENCODE_SERVER="http://localhost:3000"
.\tui.exe
```

### 3. Interact with the TUI

Once the TUI starts:
- Type a message and press Enter
- Try slash commands
- Create/delete sessions
- Watch the server terminal for detailed logs!

## What You'll See

The server logs every request with details:

```
================================================================================
[14:23:45.123] POST /session/sess_123456/message
================================================================================
{
  "body": {
    "messageID": "msg_789",
    "agent": "test-agent",
    "model": {
      "providerID": "test",
      "modelID": "test-model"
    },
    "parts": [
      {
        "type": "text",
        "text": "Hello world"
      }
    ]
  }
}

MESSAGE RECEIVED for session: sess_123456

Message Details:
   Message ID: msg_789
   Agent: test-agent
   Model: test/test-model

Parts (1):
   Part 1:
      Type: text
      Text: Hello world
```

## Next Steps

Once you understand the protocol:

1. Replace dummy responses with actual CrewAI calls
2. Implement proper session storage
3. Add streaming responses via SSE
4. Handle file operations and tools

## Endpoints Implemented

See `../OPENCODE_ENDPOINTS.md` for full API documentation.

Currently logging:
- Project endpoints
- Agent listing
- Session management
- Message sending
- Commands
- SSE event stream
- Configuration
- All other endpoints return empty/dummy responses
