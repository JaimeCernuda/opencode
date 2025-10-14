# OpenCode TUI API Endpoints

Complete documentation of all REST API endpoints that the OpenCode TUI expects to communicate with.

## Base URL
All endpoints are relative to the base server URL (e.g., `http://localhost:3000`)

## Common Query Parameters
- `directory` (optional): Working directory path for the session

---

## Project Endpoints

### `GET /project`
**List all projects**
- **Response**: Array of Project objects
```json
[{
  "id": "string",
  "worktree": "string",
  "vcs": "git" | "none",
  "initialized": boolean
}]
```

### `GET /project/current`
**Get the current project**
- **Response**: Project object
```json
{
  "id": "string",
  "worktree": "string",
  "vcs": "git" | "none",
  "initialized": boolean
}
```

---

## Configuration Endpoints

### `GET /config`
**Get configuration**
- **Response**: Config object with keybinds, theme, model settings

### `PATCH /config`
**Update configuration**
- **Request Body**: Partial config object
- **Response**: Updated config object

### `GET /config/providers`
**List all AI providers and models**
- **Response**:
```json
{
  "providers": [{
    "id": "string",
    "name": "string",
    "models": {
      "model_id": {
        "id": "string",
        "name": "string"
      }
    }
  }],
  "default": {
    "provider_id": "default_model_id"
  }
}
```

---

## Path Endpoints

### `GET /path`
**Get filesystem paths**
- **Response**:
```json
{
  "state": "string",     // State directory path
  "config": "string",    // Config directory path
  "worktree": "string",  // Git worktree path
  "directory": "string"  // Current working directory
}
```

---

## Session Endpoints

### `GET /session`
**List all sessions**
- **Response**: Array of Session objects sorted by updated time

### `POST /session`
**Create a new session**
- **Request Body** (optional):
```json
{
  "parentID": "string",  // Optional parent session ID
  "title": "string"      // Optional title
}
```
- **Response**: Session object
```json
{
  "id": "string",
  "projectID": "string",
  "directory": "string",
  "parentID": "string",  // Optional
  "title": "string",
  "version": "string",
  "time": {
    "created": number,   // Unix timestamp in ms
    "updated": number,
    "compacting": number  // Optional
  }
}
```

### `GET /session/:id`
**Get a specific session**
- **Response**: Session object

### `DELETE /session/:id`
**Delete a session**
- **Response**: `true`

### `PATCH /session/:id`
**Update session properties**
- **Request Body**:
```json
{
  "title": "string"  // Optional
}
```
- **Response**: Updated Session object

### `GET /session/:id/children`
**Get child sessions**
- **Response**: Array of Session objects

### `GET /session/:id/todo`
**Get session's todo list**
- **Response**: Array of Todo objects

### `POST /session/:id/init`
**Initialize project (analyze and create AGENTS.md)**
- **Request Body**:
```json
{
  "messageID": "string",
  "providerID": "string",
  "modelID": "string"
}
```
- **Response**: `true`

### `POST /session/:id/fork`
**Fork a session at a specific message**
- **Request Body**:
```json
{
  "messageID": "string"  // Optional - where to fork from
}
```
- **Response**: New Session object

### `POST /session/:id/abort`
**Abort/cancel a running session**
- **Response**: `true`

### `POST /session/:id/share`
**Share a session (get public URL)**
- **Response**: Updated Session object with share info

### `DELETE /session/:id/share`
**Unshare a session**
- **Response**: Updated Session object

### `POST /session/:id/summarize`
**Summarize/compact session history**
- **Request Body**:
```json
{
  "providerID": "string",
  "modelID": "string"
}
```
- **Response**: `true`

### `POST /session/:id/revert`
**Revert to a previous message**
- **Request Body**:
```json
{
  "messageID": "string",
  "partID": "string"  // Optional
}
```
- **Response**: Updated Session object

### `POST /session/:id/unrevert`
**Restore reverted messages**
- **Response**: Updated Session object

---

## Message Endpoints

### `GET /session/:id/message`
**List all messages in a session**
- **Response**: Array of Message objects with parts
```json
[{
  "info": {
    "id": "string",
    "sessionID": "string",
    "role": "user" | "assistant",
    "time": {
      "created": number,
      "completed": number  // For assistant messages
    }
  },
  "parts": [/* Part objects */]
}]
```

### `GET /session/:id/message/:messageID`
**Get a specific message**
- **Response**: Message object with parts

### `POST /session/:id/message`
**Send a prompt/message to the session**
- **Request Body**:
```json
{
  "messageID": "string",
  "model": {
    "providerID": "string",
    "modelID": "string"
  },
  "agent": "string",  // Agent name
  "parts": [{
    "id": "string",
    "type": "text" | "file" | "image",
    "text": "string",     // For text parts
    "path": "string",     // For file parts
    "content": "string"   // For file/image parts
  }]
}
```
- **Response**: Assistant message object with parts

### `POST /session/:id/command`
**Execute a slash command**
- **Request Body**:
```json
{
  "command": "string",    // Command name
  "arguments": "string",  // Command arguments
  "agent": "string",
  "model": "string"       // Format: "provider/model"
}
```
- **Response**: Assistant message object

### `POST /session/:id/shell`
**Execute a shell command**
- **Request Body**:
```json
{
  "agent": "string",
  "command": "string"
}
```
- **Response**: Assistant message object

---

## Permission Endpoints

### `POST /session/:id/permissions/:permissionID`
**Respond to a permission request**
- **Request Body**:
```json
{
  "response": "allow" | "deny" | "allow_all"
}
```
- **Response**: `true`

---

## Agent Endpoints

### `GET /agent`
**List all available agents**
- **Response**: Array of Agent objects
```json
[{
  "name": "string",
  "description": "string",
  "mode": "primary" | "subagent" | "all",
  "model": {
    "providerID": "string",
    "modelID": "string"
  }
}]
```

---

## Command Endpoints

### `GET /command`
**List all custom slash commands**
- **Response**: Array of Command objects
```json
[{
  "name": "string",
  "description": "string",
  "prompt": "string"
}]
```

---

## File Operations

### `GET /file?path=<path>`
**List files and directories**
- **Query**: `path` - Directory path
- **Response**: Array of file/directory nodes

### `GET /file/content?path=<path>`
**Read file content**
- **Query**: `path` - File path
- **Response**: File content object

### `GET /file/status`
**Get git file status**
- **Response**: Array of file info with git status

---

## Search Endpoints

### `GET /find?pattern=<pattern>`
**Search text in files (ripgrep)**
- **Query**: `pattern` - Search pattern
- **Response**: Array of matches

### `GET /find/file?query=<query>`
**Find files by name**
- **Query**: `query` - File name pattern
- **Response**: Array of file paths

### `GET /find/symbol?query=<query>`
**Find workspace symbols (LSP)**
- **Query**: `query` - Symbol name
- **Response**: Array of symbol objects

---

## Tool Endpoints

### `GET /experimental/tool/ids`
**List all available tool IDs**
- **Response**: Array of tool ID strings

### `GET /experimental/tool?provider=<provider>&model=<model>`
**List tools with JSON schemas for a provider/model**
- **Query**: `provider`, `model`
- **Response**: Array of tool definitions
```json
[{
  "id": "string",
  "description": "string",
  "parameters": {}  // JSON Schema
}]
```

---

## TUI Control Endpoints
*(Used for bidirectional TUI communication)*

### `POST /tui/append-prompt`
**Append text to TUI prompt**
- **Request Body**: `{ "text": "string" }`

### `POST /tui/open-help`
**Open help dialog**

### `POST /tui/open-sessions`
**Open sessions dialog**

### `POST /tui/open-themes`
**Open themes dialog**

### `POST /tui/open-models`
**Open models dialog**

### `POST /tui/submit-prompt`
**Submit the current prompt**

### `POST /tui/clear-prompt`
**Clear the prompt input**

### `POST /tui/execute-command`
**Execute a TUI command**
- **Request Body**: `{ "command": "string" }`

### `POST /tui/show-toast`
**Show a toast notification**
- **Request Body**:
```json
{
  "title": "string",
  "message": "string",
  "variant": "info" | "success" | "warning" | "error"
}
```

### `GET /tui/control/next`
**Get next TUI control request** *(polling endpoint)*
- **Response**: Request object

### `POST /tui/control/response`
**Send response to TUI control request**
- **Request Body**: Response object

---

## Logging Endpoints

### `POST /log`
**Write a log entry**
- **Request Body**:
```json
{
  "service": "string",
  "level": "debug" | "info" | "error" | "warn",
  "message": "string",
  "extra": {}  // Optional metadata
}
```
- **Response**: `true`

---

## Authentication Endpoints

### `PUT /auth/:id`
**Set authentication credentials**
- **Request Body**: Auth info object
- **Response**: `true`

---

## MCP Endpoints

### `GET /mcp`
**Get MCP (Model Context Protocol) server status**
- **Response**: MCP status object

---

## Event Stream (Server-Sent Events)

### `GET /event`
**Subscribe to real-time events**
- **Response**: Server-Sent Events stream
- **Event Format**:
```json
{
  "type": "event.type",
  "properties": {
    // Event-specific data
  }
}
```

**Common Events:**
- `server.connected` - Initial connection established
- `session.updated` - Session data changed
- `message.updated` - Message updated
- `message.part.updated` - Message part updated (tool calls, text chunks)
- `session.error` - Error occurred in session

---

## OpenAPI Documentation

### `GET /doc`
**Get OpenAPI/Swagger documentation**
- **Response**: Interactive API documentation UI

---

## Required Core Endpoints for Basic TUI Functionality

The minimum set of endpoints needed for the TUI to function:

1. **Essential**:
   - `GET /project/current`
   - `GET /agent`
   - `GET /path`
   - `GET /config/providers`
   - `POST /session`
   - `GET /session/:id/message`
   - `POST /session/:id/message`
   - `POST /session/:id/abort`
   - `GET /event`

2. **Important for UX**:
   - `GET /session`
   - `DELETE /session/:id`
   - `PATCH /session/:id`
   - `GET /command`
   - `POST /session/:id/command`

3. **Optional but enhancing**:
   - File operations
   - Search endpoints
   - TUI control endpoints
   - Sharing/forking

---

## Data Types Reference

### Session Object
```typescript
{
  id: string
  projectID: string
  directory: string
  parentID?: string
  share?: { url: string }
  title: string
  version: string
  time: {
    created: number
    updated: number
    compacting?: number
  }
  revert?: {
    messageID: string
    partID?: string
    snapshot?: string
    diff?: string
  }
}
```

### Message Part Types
```typescript
// Text part
{
  id: string
  type: "text"
  text: string
  time?: { start: number, end: number }
}

// Tool part
{
  id: string
  type: "tool"
  tool: string  // Tool name
  state: {
    status: "pending" | "running" | "completed" | "error"
    title?: string
    input: object
    output?: string
    error?: string
  }
}

// File part
{
  id: string
  type: "file"
  path: string
  content: string
}

// Image part
{
  id: string
  type: "image"
  media_type: string
  data: string  // Base64 encoded
}
```

---

## Notes

1. **All timestamps are in milliseconds** (Unix epoch)
2. **IDs use ascending sort order** - newer IDs are lexicographically greater
3. **SSE stream is critical** - The TUI relies on real-time events for updates
4. **Directory context** - Many endpoints accept optional `?directory=` query param
5. **CORS enabled** - Server has CORS middleware for cross-origin requests
