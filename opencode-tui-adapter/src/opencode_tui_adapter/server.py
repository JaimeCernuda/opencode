"""
OpenCode TUI Adapter - Logging Server
Minimal server that logs all TUI requests to help understand the protocol
"""
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import time
from datetime import datetime
from typing import Any

app = FastAPI(title="OpenCode TUI Logging Adapter")

# Enable CORS for the TUI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def log_request(method: str, path: str, data: Any = None):
    """Pretty print request details"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"\n{'='*80}")
    print(f"[{timestamp}] {method} {path}")
    print(f"{'='*80}")
    if data:
        print(json.dumps(data, indent=2))
    print()


def generate_id(prefix: str = "msg") -> str:
    """Generate a time-based ID"""
    return f"{prefix}_{int(time.time() * 1000)}"


# Catch-all logging middleware
@app.middleware("http")
async def log_all_requests(request: Request, call_next):
    # Try to read body if present
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body_bytes = await request.body()
            if body_bytes:
                body = json.loads(body_bytes.decode())
        except:
            pass

    log_request(
        request.method,
        request.url.path + (f"?{request.url.query}" if request.url.query else ""),
        {"body": body, "query": dict(request.query_params)} if body or request.query_params else None
    )

    response = await call_next(request)
    return response


# ============================================================================
# CORE REQUIRED ENDPOINTS
# ============================================================================

@app.get("/project/current")
async def get_current_project():
    """Return a dummy project"""
    return {
        "id": "project_test",
        "worktree": "C:/Users/jaime/OneDrive/Documents/Projects/opencode",
        "vcs": "git",
        "initialized": True
    }


@app.get("/agent")
async def list_agents():
    """Return dummy agents"""
    return [
        {
            "name": "test-agent",
            "description": "Test agent for logging",
            "mode": "primary",
            "model": {
                "providerID": "test",
                "modelID": "test-model"
            }
        }
    ]


@app.get("/path")
async def get_paths():
    """Return filesystem paths"""
    return {
        "state": "C:/Users/jaime/.opencode/state",
        "config": "C:/Users/jaime/.opencode/config",
        "worktree": "C:/Users/jaime/OneDrive/Documents/Projects/opencode",
        "directory": "C:/Users/jaime/OneDrive/Documents/Projects/opencode"
    }


@app.get("/config")
async def get_config():
    """Return dummy config"""
    return {
        "theme": "system",
        "share": "disabled",
        "model": "",
        "keybinds": {
            "leader": "ctrl+x"
        },
        "tui": {
            "scrollSpeed": 3
        }
    }


@app.get("/config/providers")
async def list_providers():
    """Return dummy providers"""
    return {
        "providers": [
            {
                "id": "test-provider",
                "name": "Test Provider",
                "models": {
                    "test-model": {
                        "id": "test-model",
                        "name": "Test Model"
                    }
                }
            }
        ],
        "default": {
            "test-provider": "test-model"
        }
    }


@app.get("/session")
async def list_sessions():
    """Return empty sessions list"""
    return []


@app.post("/session")
async def create_session(request: Request):
    """Create a new session"""
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    session_id = generate_id("session")

    print(f"📝 SESSION CREATED: {session_id}")
    if body:
        print(f"   Request body: {json.dumps(body, indent=2)}")

    return {
        "id": session_id,
        "projectID": "project_test",
        "directory": "C:/Users/jaime/OneDrive/Documents/Projects/opencode",
        "title": body.get("title", f"New session {session_id[:8]}"),
        "version": "0.1.0",
        "time": {
            "created": int(time.time() * 1000),
            "updated": int(time.time() * 1000)
        }
    }


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get a session"""
    return {
        "id": session_id,
        "projectID": "project_test",
        "directory": "C:/Users/jaime/OneDrive/Documents/Projects/opencode",
        "title": f"Session {session_id[:8]}",
        "version": "0.1.0",
        "time": {
            "created": int(time.time() * 1000),
            "updated": int(time.time() * 1000)
        }
    }


@app.get("/session/{session_id}/message")
async def list_messages(session_id: str):
    """Return empty messages list"""
    print(f"📬 MESSAGES REQUESTED for session: {session_id}")
    return []


@app.post("/session/{session_id}/message")
async def send_message(session_id: str, request: Request):
    """Handle incoming prompt"""
    body = await request.json()

    print(f"\n{'🚀 '*20}")
    print(f"💬 MESSAGE RECEIVED for session: {session_id}")
    print(f"{'🚀 '*20}")
    print(f"\n📋 Message Details:")
    print(f"   Message ID: {body.get('messageID')}")
    print(f"   Agent: {body.get('agent')}")
    print(f"   Model: {body.get('model', {}).get('providerID')}/{body.get('model', {}).get('modelID')}")

    parts = body.get('parts', [])
    print(f"\n📦 Parts ({len(parts)}):")
    for i, part in enumerate(parts, 1):
        print(f"   Part {i}:")
        print(f"      Type: {part.get('type')}")
        if part.get('type') == 'text':
            print(f"      Text: {part.get('text')[:100]}..." if len(part.get('text', '')) > 100 else f"      Text: {part.get('text')}")
        elif part.get('type') == 'file':
            print(f"      Path: {part.get('path')}")

    message_id = body.get('messageID', generate_id('msg'))

    # Return a simple echo response
    return {
        "info": {
            "id": message_id,
            "sessionID": session_id,
            "role": "assistant",
            "time": {
                "created": int(time.time() * 1000),
                "completed": int(time.time() * 1000)
            }
        },
        "parts": [
            {
                "id": generate_id("part"),
                "type": "text",
                "text": f"✅ Logged your message! I received: {parts[0].get('text', 'No text')[:50] if parts else 'No content'}"
            }
        ]
    }


@app.post("/session/{session_id}/abort")
async def abort_session(session_id: str):
    """Abort a session"""
    print(f"🛑 ABORT REQUESTED for session: {session_id}")
    return True


@app.post("/session/{session_id}/command")
async def execute_command(session_id: str, request: Request):
    """Handle slash command"""
    body = await request.json()

    print(f"\n{'⚡ '*20}")
    print(f"🎯 COMMAND RECEIVED for session: {session_id}")
    print(f"{'⚡ '*20}")
    print(f"   Command: {body.get('command')}")
    print(f"   Arguments: {body.get('arguments')}")
    print(f"   Agent: {body.get('agent')}")

    message_id = generate_id('msg')
    return {
        "info": {
            "id": message_id,
            "sessionID": session_id,
            "role": "assistant",
            "time": {
                "created": int(time.time() * 1000),
                "completed": int(time.time() * 1000)
            }
        },
        "parts": [
            {
                "id": generate_id("part"),
                "type": "text",
                "text": f"✅ Command logged: /{body.get('command')} {body.get('arguments', '')}"
            }
        ]
    }


@app.get("/command")
async def list_commands():
    """Return empty commands list"""
    return []


# ============================================================================
# SERVER-SENT EVENTS (SSE) - Critical for TUI
# ============================================================================

@app.get("/event")
async def event_stream(request: Request):
    """SSE stream for real-time updates"""
    print("\n🌊 SSE STREAM CONNECTED")

    async def event_generator():
        # Send initial connection event
        yield {
            "event": "message",
            "data": json.dumps({
                "type": "server.connected",
                "properties": {}
            })
        }
        print("   ✅ Sent: server.connected")

        # Keep connection alive
        try:
            while True:
                if await request.is_disconnected():
                    print("\n🌊 SSE STREAM DISCONNECTED")
                    break
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            print("\n🌊 SSE STREAM CANCELLED")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# ============================================================================
# OPTIONAL ENDPOINTS (to prevent errors)
# ============================================================================

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    print(f"🗑️  DELETE SESSION: {session_id}")
    return True


@app.patch("/session/{session_id}")
async def update_session(session_id: str, request: Request):
    """Update session"""
    body = await request.json()
    print(f"✏️  UPDATE SESSION: {session_id}")
    print(f"   Updates: {json.dumps(body, indent=2)}")

    return {
        "id": session_id,
        "projectID": "project_test",
        "directory": "C:/Users/jaime/OneDrive/Documents/Projects/opencode",
        "title": body.get("title", f"Session {session_id[:8]}"),
        "version": "0.1.0",
        "time": {
            "created": int(time.time() * 1000),
            "updated": int(time.time() * 1000)
        }
    }


@app.post("/log")
async def log_entry(request: Request):
    """Handle log entries from TUI"""
    body = await request.json()
    level = body.get('level', 'info').upper()
    service = body.get('service', 'unknown')
    message = body.get('message', '')

    print(f"📋 TUI LOG [{level}] [{service}]: {message}")
    if body.get('extra'):
        print(f"   Extra: {json.dumps(body.get('extra'), indent=2)}")

    return True


@app.get("/mcp")
async def mcp_status():
    """MCP status"""
    return {}


# ============================================================================
# PROJECT ENDPOINTS
# ============================================================================

@app.get("/project")
async def list_projects():
    """List all projects"""
    print("📁 LIST PROJECTS")
    return [{
        "id": "project_test",
        "worktree": "C:/Users/jaime/OneDrive/Documents/Projects/opencode",
        "vcs": "git",
        "initialized": True
    }]


# ============================================================================
# CONFIGURATION ENDPOINTS
# ============================================================================

@app.patch("/config")
async def update_config(request: Request):
    """Update configuration"""
    body = await request.json()
    print(f"⚙️  CONFIG UPDATE")
    print(f"   Updates: {json.dumps(body, indent=2)}")
    return body


# ============================================================================
# SESSION EXTENDED ENDPOINTS
# ============================================================================

@app.get("/session/{session_id}/children")
async def get_session_children(session_id: str):
    """Get child sessions"""
    print(f"👶 CHILDREN REQUESTED for session: {session_id}")
    return []


@app.get("/session/{session_id}/todo")
async def get_session_todos(session_id: str):
    """Get session todos"""
    print(f"✅ TODOS REQUESTED for session: {session_id}")
    return []


@app.post("/session/{session_id}/init")
async def initialize_session(session_id: str, request: Request):
    """Initialize project"""
    body = await request.json()
    print(f"🏗️  INIT REQUESTED for session: {session_id}")
    print(f"   Provider: {body.get('providerID')}/{body.get('modelID')}")
    return True


@app.post("/session/{session_id}/fork")
async def fork_session(session_id: str, request: Request):
    """Fork a session"""
    body = await request.json()
    fork_id = generate_id("session")
    print(f"🍴 FORK REQUESTED")
    print(f"   Source: {session_id}")
    print(f"   New ID: {fork_id}")
    print(f"   At message: {body.get('messageID', 'none')}")

    return {
        "id": fork_id,
        "projectID": "project_test",
        "directory": "C:/Users/jaime/OneDrive/Documents/Projects/opencode",
        "parentID": session_id,
        "title": f"Fork of {session_id[:8]}",
        "version": "0.1.0",
        "time": {
            "created": int(time.time() * 1000),
            "updated": int(time.time() * 1000)
        }
    }


@app.post("/session/{session_id}/share")
async def share_session(session_id: str):
    """Share a session"""
    print(f"🔗 SHARE REQUESTED for session: {session_id}")
    return {
        "id": session_id,
        "projectID": "project_test",
        "directory": "C:/Users/jaime/OneDrive/Documents/Projects/opencode",
        "title": f"Session {session_id[:8]}",
        "version": "0.1.0",
        "share": {
            "url": f"https://opencode.ai/s/{session_id[:8]}"
        },
        "time": {
            "created": int(time.time() * 1000),
            "updated": int(time.time() * 1000)
        }
    }


@app.delete("/session/{session_id}/share")
async def unshare_session(session_id: str):
    """Unshare a session"""
    print(f"🔓 UNSHARE REQUESTED for session: {session_id}")
    return {
        "id": session_id,
        "projectID": "project_test",
        "directory": "C:/Users/jaime/OneDrive/Documents/Projects/opencode",
        "title": f"Session {session_id[:8]}",
        "version": "0.1.0",
        "time": {
            "created": int(time.time() * 1000),
            "updated": int(time.time() * 1000)
        }
    }


@app.post("/session/{session_id}/summarize")
async def summarize_session(session_id: str, request: Request):
    """Summarize/compact session"""
    body = await request.json()
    print(f"📝 SUMMARIZE REQUESTED for session: {session_id}")
    print(f"   Using: {body.get('providerID')}/{body.get('modelID')}")
    return True


@app.post("/session/{session_id}/revert")
async def revert_session(session_id: str, request: Request):
    """Revert to previous message"""
    body = await request.json()
    print(f"⏪ REVERT REQUESTED for session: {session_id}")
    print(f"   To message: {body.get('messageID')}")
    print(f"   Part: {body.get('partID', 'all')}")

    return {
        "id": session_id,
        "projectID": "project_test",
        "directory": "C:/Users/jaime/OneDrive/Documents/Projects/opencode",
        "title": f"Session {session_id[:8]}",
        "version": "0.1.0",
        "revert": {
            "messageID": body.get('messageID'),
            "partID": body.get('partID')
        },
        "time": {
            "created": int(time.time() * 1000),
            "updated": int(time.time() * 1000)
        }
    }


@app.post("/session/{session_id}/unrevert")
async def unrevert_session(session_id: str):
    """Restore reverted messages"""
    print(f"⏩ UNREVERT REQUESTED for session: {session_id}")
    return {
        "id": session_id,
        "projectID": "project_test",
        "directory": "C:/Users/jaime/OneDrive/Documents/Projects/opencode",
        "title": f"Session {session_id[:8]}",
        "version": "0.1.0",
        "time": {
            "created": int(time.time() * 1000),
            "updated": int(time.time() * 1000)
        }
    }


# ============================================================================
# MESSAGE ENDPOINTS
# ============================================================================

@app.get("/session/{session_id}/message/{message_id}")
async def get_message(session_id: str, message_id: str):
    """Get specific message"""
    print(f"📨 MESSAGE REQUESTED: {message_id} in session: {session_id}")
    return {
        "info": {
            "id": message_id,
            "sessionID": session_id,
            "role": "user",
            "time": {
                "created": int(time.time() * 1000)
            }
        },
        "parts": []
    }


@app.post("/session/{session_id}/shell")
async def execute_shell(session_id: str, request: Request):
    """Execute shell command"""
    body = await request.json()
    print(f"\n{'💻 '*20}")
    print(f"🖥️  SHELL COMMAND for session: {session_id}")
    print(f"{'💻 '*20}")
    print(f"   Command: {body.get('command')}")
    print(f"   Agent: {body.get('agent')}")

    return {
        "id": generate_id('msg'),
        "sessionID": session_id,
        "role": "assistant",
        "time": {
            "created": int(time.time() * 1000),
            "completed": int(time.time() * 1000)
        }
    }


# ============================================================================
# PERMISSION ENDPOINTS
# ============================================================================

@app.post("/session/{session_id}/permissions/{permission_id}")
async def respond_to_permission(session_id: str, permission_id: str, request: Request):
    """Respond to permission request"""
    body = await request.json()
    print(f"🔐 PERMISSION RESPONSE for session: {session_id}")
    print(f"   Permission ID: {permission_id}")
    print(f"   Response: {body.get('response')}")
    return True


# ============================================================================
# FILE OPERATIONS
# ============================================================================

@app.get("/file")
async def list_files(path: str = ""):
    """List files and directories"""
    print(f"📂 LIST FILES: {path or '(root)'}")
    return []


@app.get("/file/content")
async def read_file(path: str):
    """Read file content"""
    print(f"📄 READ FILE: {path}")
    return {
        "path": path,
        "content": "# File content would go here",
        "type": "text"
    }


@app.get("/file/status")
async def file_status():
    """Get git file status"""
    print("📊 FILE STATUS (git)")
    return []


# ============================================================================
# SEARCH ENDPOINTS
# ============================================================================

@app.get("/find")
async def search_text(pattern: str):
    """Search text in files (ripgrep)"""
    print(f"🔍 SEARCH TEXT: {pattern}")
    return []


@app.get("/find/file")
async def find_files(query: str):
    """Find files by name"""
    print(f"🔍 FIND FILES: {query}")
    return []


@app.get("/find/symbol")
async def find_symbols(query: str):
    """Find workspace symbols (LSP)"""
    print(f"🔍 FIND SYMBOLS: {query}")
    return []


# ============================================================================
# TOOL ENDPOINTS
# ============================================================================

@app.get("/experimental/tool/ids")
async def list_tool_ids():
    """List all tool IDs"""
    print("🔧 LIST TOOL IDS")
    return ["bash", "read", "write", "edit", "grep", "glob"]


@app.get("/experimental/tool")
async def list_tools(provider: str, model: str):
    """List tools for provider/model"""
    print(f"🔧 LIST TOOLS for {provider}/{model}")
    return [
        {
            "id": "bash",
            "description": "Execute bash commands",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"}
                }
            }
        }
    ]


# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@app.put("/auth/{auth_id}")
async def set_auth(auth_id: str, request: Request):
    """Set authentication credentials"""
    body = await request.json()
    print(f"🔑 SET AUTH: {auth_id}")
    print(f"   Type: {body.get('type', 'unknown')}")
    return True


# ============================================================================
# TUI CONTROL ENDPOINTS
# ============================================================================

@app.post("/tui/append-prompt")
async def tui_append_prompt(request: Request):
    """Append text to TUI prompt"""
    body = await request.json()
    print(f"📝 TUI APPEND: {body.get('text', '')[:50]}")
    return True


@app.post("/tui/open-help")
async def tui_open_help():
    """Open help dialog"""
    print("❓ TUI OPEN HELP")
    return True


@app.post("/tui/open-sessions")
async def tui_open_sessions():
    """Open sessions dialog"""
    print("📋 TUI OPEN SESSIONS")
    return True


@app.post("/tui/open-themes")
async def tui_open_themes():
    """Open themes dialog"""
    print("🎨 TUI OPEN THEMES")
    return True


@app.post("/tui/open-models")
async def tui_open_models():
    """Open models dialog"""
    print("🤖 TUI OPEN MODELS")
    return True


@app.post("/tui/submit-prompt")
async def tui_submit_prompt():
    """Submit the current prompt"""
    print("📤 TUI SUBMIT PROMPT")
    return True


@app.post("/tui/clear-prompt")
async def tui_clear_prompt():
    """Clear the prompt input"""
    print("🗑️  TUI CLEAR PROMPT")
    return True


@app.post("/tui/execute-command")
async def tui_execute_command(request: Request):
    """Execute a TUI command"""
    body = await request.json()
    print(f"⚡ TUI EXECUTE: {body.get('command')}")
    return True


@app.post("/tui/show-toast")
async def tui_show_toast(request: Request):
    """Show toast notification"""
    body = await request.json()
    print(f"🍞 TUI TOAST [{body.get('variant', 'info').upper()}]: {body.get('message')}")
    return True


@app.get("/tui/control/next")
async def tui_control_next():
    """Get next TUI control request (polling)"""
    # This is a long-polling endpoint - return empty for now
    await asyncio.sleep(0.1)
    return {}


@app.post("/tui/control/response")
async def tui_control_response(request: Request):
    """Send response to TUI control request"""
    body = await request.json()
    print(f"🎮 TUI CONTROL RESPONSE")
    return True


# ============================================================================
# CATCH-ALL for any remaining unimplemented endpoints
# ============================================================================

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def catch_all(path: str, request: Request):
    """Catch any unimplemented endpoints"""
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.json()
        except:
            pass

    print(f"\n⚠️  UNIMPLEMENTED ENDPOINT")
    print(f"   Method: {request.method}")
    print(f"   Path: /{path}")
    if body:
        print(f"   Body: {json.dumps(body, indent=2)}")

    # Return empty success response
    return {}


if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*80)
    print("🚀 OpenCode TUI Logging Server Starting...")
    print("="*80)
    print("\nThis server will log all requests from the TUI")
    print("To connect the TUI, run:")
    print("  OPENCODE_SERVER=http://localhost:3000 <path-to-tui-binary>")
    print("\n" + "="*80 + "\n")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=3000,
        log_level="warning"  # Reduce uvicorn logs to focus on our logs
    )
