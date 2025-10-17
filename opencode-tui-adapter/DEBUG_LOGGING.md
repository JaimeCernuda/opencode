# Debug Logging Guide

## Overview

The OpenCode TUI Adapter includes comprehensive debug logging capabilities that provide full system tracing. This allows you to track every function call, input, output, and internal state change throughout the application.

## Enabling Debug Logging

Debug logging is controlled via the `OPENCODE_LOG_LEVEL` environment variable.

### Set Log Level to DEBUG

```bash
# Enable debug logging
export OPENCODE_LOG_LEVEL=DEBUG

# Run the server
uv run opencode-tui-adapter
```

### Available Log Levels

- **ERROR**: Only error messages
- **WARNING**: Warnings and errors
- **INFO**: Normal operational messages (default)
- **DEBUG**: Detailed trace of all function calls and internal operations

## What Gets Logged at DEBUG Level

### Function Tracing

Every function decorated with `@trace_function` logs:
- **Entry**: Function name, module, and all input arguments
- **Exit**: Return value (truncated to 200 characters)
- **Exceptions**: Any exceptions raised with type and message

Example output:
```json
{
  "event": "function_entry",
  "function": "create_session",
  "module": "opencode_tui_adapter.session.manager",
  "args": {"title": "Test Session", "agent_name": "build"},
  "timestamp": "2025-10-17T10:30:45.123456Z",
  "level": "debug"
}
```

### Component-Specific Logging

#### Server Endpoints (`server.py`)
- HTTP request details (method, path, query params, body preview)
- Endpoint execution flow
- Response preparation
- Session lookups
- Message sending/receiving

#### Session Manager (`session/manager.py`)
- Session creation steps:
  - ID generation
  - Agent configuration lookup
  - Session context creation
  - Claude SDK client initialization
  - Connection establishment
- Session operations:
  - Get/list/update/delete operations
  - Client disconnection
  - Metadata changes

#### Event Bus (`events/bus.py`)
- Subscriber management:
  - New subscriptions with queue IDs
  - Unsubscribe operations
- Event broadcasting:
  - Event type and subscriber count
  - Individual queue operations
  - Success/failure tracking

#### Message Translation (`utils/translation.py`)
- SDK message type identification
- Block-by-block conversion:
  - Text blocks with previews
  - Thinking blocks
  - Tool use blocks
  - Tool result blocks
- TUI message creation
- Timing information

## Example Debug Session

### Starting the Server

```bash
export OPENCODE_LOG_LEVEL=DEBUG
uv run opencode-tui-adapter
```

### Sample Debug Output

```json
{"event": "function_entry", "function": "create_session", "args": {"title": "My Session"}, "level": "debug"}
{"event": "create_session_start", "title": "My Session", "agent_name": "build", "level": "debug"}
{"event": "create_session_id_generated", "session_id": "session_abc123", "level": "debug"}
{"event": "create_session_agent_found", "agent_name": "build", "model": "claude-3-5-sonnet", "level": "debug"}
{"event": "create_session_context_created", "session_id": "session_abc123", "directory": "/home/user/workspace", "level": "debug"}
{"event": "create_session_sdk_options_created", "session_id": "session_abc123", "tools_count": 6, "level": "debug"}
{"event": "create_session_sdk_client_created", "session_id": "session_abc123", "level": "debug"}
{"event": "create_session_connecting_sdk", "session_id": "session_abc123", "level": "debug"}
{"event": "create_session_sdk_connected", "session_id": "session_abc123", "level": "debug"}
{"event": "create_session_stored", "session_id": "session_abc123", "total_sessions": 1, "level": "debug"}
{"event": "session_created", "session_id": "session_abc123", "title": "My Session", "level": "info"}
{"event": "function_exit", "function": "create_session", "result": "<SessionContext id=session_abc123>", "level": "debug"}
```

## Filtering Logs

### Using jq for JSON Parsing

```bash
# Filter only function entry/exit
uv run opencode-tui-adapter 2>&1 | jq 'select(.event | contains("function"))'

# Filter by specific session
uv run opencode-tui-adapter 2>&1 | jq 'select(.session_id == "session_abc123")'

# Filter by log level
uv run opencode-tui-adapter 2>&1 | jq 'select(.level == "debug")'
```

### Using grep

```bash
# Find all session creation events
uv run opencode-tui-adapter 2>&1 | grep "create_session"

# Find all SDK-related operations
uv run opencode-tui-adapter 2>&1 | grep "sdk"

# Find all errors
uv run opencode-tui-adapter 2>&1 | grep '"level":"error"'
```

## Performance Considerations

Debug logging generates **significant output** and may impact performance:

- **File I/O**: Each log write is a system call
- **String formatting**: JSON serialization for every log entry
- **Function decorator overhead**: Inspection and formatting on every call

### Recommendations

1. **Development**: Use DEBUG level freely
2. **Testing**: Use INFO or DEBUG as needed
3. **Production**: Use INFO or WARNING level
4. **Performance testing**: Use WARNING or ERROR only

## Log Output Format

All logs are structured JSON with the following standard fields:

```json
{
  "event": "event_name",           // Event identifier
  "timestamp": "ISO8601 timestamp", // When the event occurred
  "level": "debug|info|warning|error", // Log level
  "logger": "module.name",          // Logger name
  // ... event-specific fields
}
```

## Verifying Debug Logging

### Quick Test

```bash
# Set debug level
export OPENCODE_LOG_LEVEL=DEBUG

# Start server and make a request
uv run opencode-tui-adapter &
SERVER_PID=$!

sleep 2  # Wait for server to start

# Make test request
curl http://localhost:3000/project/current

# Check logs for debug events
kill $SERVER_PID
```

You should see detailed function_entry and function_exit logs for every function called.

## Troubleshooting

### No Debug Logs Appearing

1. **Check environment variable**:
   ```bash
   echo $OPENCODE_LOG_LEVEL
   # Should output: DEBUG
   ```

2. **Verify log level in startup message**:
   ```json
   {"event": "server_starting", "log_level": "DEBUG", ...}
   ```

3. **Check if logs are being written to stderr**:
   ```bash
   uv run opencode-tui-adapter 2>&1 | head -20
   ```

### Too Much Output

1. **Increase log level**:
   ```bash
   export OPENCODE_LOG_LEVEL=INFO
   ```

2. **Filter to specific components**:
   ```bash
   uv run opencode-tui-adapter 2>&1 | jq 'select(.logger | contains("session"))'
   ```

## Integration with Testing

Debug logging is automatically active during testing if you set the environment variable:

```bash
# Run tests with debug logging
OPENCODE_LOG_LEVEL=DEBUG uv run pytest tests/ -v -s
```

This helps diagnose test failures by showing the complete execution trace.

## Common Debug Patterns

### Tracking a Session Lifecycle

```bash
# Follow a session from creation to deletion
uv run opencode-tui-adapter 2>&1 | jq 'select(.session_id == "session_abc123")'
```

### Monitoring Message Flow

```bash
# See all message-related operations
uv run opencode-tui-adapter 2>&1 | jq 'select(.event | contains("message"))'
```

### Debugging SSE Streams

```bash
# Track SSE subscriber lifecycle
uv run opencode-tui-adapter 2>&1 | jq 'select(.event | contains("sse"))'
```

### Finding Performance Bottlenecks

```bash
# Look for slow operations (combine with timestamps)
uv run opencode-tui-adapter 2>&1 | jq 'select(.event | contains("function_exit"))'
```

## Summary

Debug logging provides complete visibility into the OpenCode TUI Adapter's operations:

- ✅ Full function tracing with inputs/outputs
- ✅ Internal state changes logged
- ✅ Structured JSON format for easy parsing
- ✅ Configurable via environment variable
- ✅ No code changes required to enable/disable
- ✅ Safe for production (just change log level)

Use `OPENCODE_LOG_LEVEL=DEBUG` to enable comprehensive system tracing during development and troubleshooting.
