"""
OpenCode Claude Agent Adapter - Main Server
FastAPI server that bridges OpenCode TUI with Claude Agent SDK
"""

import os
import json
import time
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

from opencode_claude_agent.models import (
    Session, Message, MessageInfo, TimeInfo,
    SendMessageRequest, CreateSessionRequest, CommandRequest,
    Project, Config, Provider, ProvidersResponse, PathsResponse,
    TextPart
)
from opencode_claude_agent.storage import SessionStorage
from opencode_claude_agent.agent import ClaudeAgentManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
storage = SessionStorage()
agent_manager: Optional[ClaudeAgentManager] = None

# SSE clients per session
sse_queues: Dict[str, asyncio.Queue] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global agent_manager

    logger.info("Starting OpenCode Claude Agent Adapter...")

    # Initialize agent manager
    try:
        agent_manager = ClaudeAgentManager()
        logger.info("Claude Agent Manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Agent Manager: {e}")
        raise

    yield

    # Cleanup
    logger.info("Shutting down OpenCode Claude Agent Adapter...")


app = FastAPI(
    title="OpenCode Claude Agent Adapter",
    description="Bridge between OpenCode TUI and Claude Agent SDK",
    version="0.1.0",
    lifespan=lifespan
)

# Enable CORS
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
    logger.info(f"[{timestamp}] {method} {path}")
    if data:
        logger.debug(f"Request data: {json.dumps(data, indent=2)}")


def generate_id(prefix: str = "msg") -> str:
    """Generate a time-based ID"""
    return f"{prefix}_{int(time.time() * 1000)}"


async def send_sse_event(session_id: str, event: Dict[str, Any]):
    """Send SSE event to all connected clients"""
    # Broadcast to all connected SSE clients
    # (Since OpenCode TUI doesn't send session_id with SSE connection)
    logger.info(f"Broadcasting SSE event to {len(sse_queues)} clients: {event.get('type')}")

    for client_id, queue in list(sse_queues.items()):
        try:
            await queue.put(event)
        except Exception as e:
            logger.error(f"Error sending SSE event to client {client_id}: {e}")


# ============================================================================
# CORE REQUIRED ENDPOINTS
# ============================================================================

@app.get("/project/current")
async def get_current_project():
    """Return current project info"""
    log_request("GET", "/project/current")

    return Project(
        id="default_project",
        worktree=os.getcwd(),
        vcs="git",
        initialized=True
    )


@app.get("/agent")
async def list_agents():
    """Return available agents"""
    log_request("GET", "/agent")

    return [
        {
            "name": "claude-agent",
            "description": "Claude AI Assistant via Agent SDK",
            "mode": "primary",
            "model": {
                "providerID": "anthropic",
                "modelID": os.getenv("CLAUDE_MODEL", "claude-opus-4-20250514")
            }
        }
    ]


@app.get("/path")
async def get_paths():
    """Return filesystem paths"""
    log_request("GET", "/path")

    home = os.path.expanduser("~")
    opencode_dir = os.path.join(home, ".opencode")

    return PathsResponse(
        state=os.path.join(opencode_dir, "state"),
        config=os.path.join(opencode_dir, "config"),
        worktree=os.getcwd(),
        directory=os.getcwd()
    )


@app.get("/config")
async def get_config():
    """Return configuration"""
    log_request("GET", "/config")

    return Config(
        theme="system",
        share="disabled",
        model="",
        keybinds={"leader": "ctrl+x"},
        tui={"scrollSpeed": 3}
    )


@app.get("/config/providers")
async def list_providers():
    """Return model providers"""
    log_request("GET", "/config/providers")

    return ProvidersResponse(
        providers=[
            Provider(
                id="anthropic",
                name="Anthropic",
                models={
                    "claude-opus-4-20250514": {
                        "id": "claude-opus-4-20250514",
                        "name": "Claude Opus 4"
                    },
                    "claude-sonnet-4-20250514": {
                        "id": "claude-sonnet-4-20250514",
                        "name": "Claude Sonnet 4"
                    }
                }
            )
        ],
        default={"anthropic": os.getenv("CLAUDE_MODEL", "claude-opus-4-20250514")}
    )


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

@app.get("/session")
async def list_sessions():
    """List all sessions"""
    log_request("GET", "/session")
    return storage.get_all_sessions()


@app.post("/session")
async def create_session(request: CreateSessionRequest):
    """Create a new session"""
    log_request("POST", "/session", request.model_dump())

    session = storage.create_session(
        title=request.title,
        directory=request.directory
    )

    logger.info(f"Created session: {session.id}")
    return session


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session details"""
    log_request("GET", f"/session/{session_id}")

    session = storage.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@app.patch("/session/{session_id}")
async def update_session(session_id: str, request: Request):
    """Update session"""
    body = await request.json()
    log_request("PATCH", f"/session/{session_id}", body)

    session = storage.update_session(session_id, **body)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    log_request("DELETE", f"/session/{session_id}")

    success = storage.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    # Clean up agent data
    if agent_manager:
        await agent_manager.clear_session(session_id)

    # Clean up SSE queue
    if session_id in sse_queues:
        del sse_queues[session_id]

    return True


# ============================================================================
# MESSAGE HANDLING
# ============================================================================

@app.get("/session/{session_id}/message")
async def list_messages(session_id: str):
    """Get messages for a session"""
    log_request("GET", f"/session/{session_id}/message")

    messages = storage.get_messages(session_id)
    return messages


@app.post("/session/{session_id}/message")
async def send_message(session_id: str, request: SendMessageRequest):
    """Send message and get AI response"""
    log_request("POST", f"/session/{session_id}/message", request.model_dump())

    if not agent_manager:
        raise HTTPException(status_code=500, detail="Agent manager not initialized")

    session = storage.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Create user message
    now = int(time.time() * 1000)
    user_message = Message(
        info=MessageInfo(
            id=request.messageID,
            sessionID=session_id,
            role="user",
            time=TimeInfo(created=now)
        ),
        parts=request.parts
    )
    storage.add_message(session_id, user_message)

    # Create assistant message with empty parts
    assistant_message_id = generate_id("msg")
    assistant_message = Message(
        info=MessageInfo(
            id=assistant_message_id,
            sessionID=session_id,
            role="assistant",
            time=TimeInfo(created=now)  # No completed time yet
        ),
        parts=[]
    )
    storage.add_message(session_id, assistant_message)

    # Send message.updated event (message created)
    await send_sse_event(session_id, {
        "type": "message.updated",
        "properties": {
            "info": {
                "id": assistant_message_id,
                "sessionID": session_id,
                "role": "assistant",
                "time": {
                    "created": now
                },
                "modelID": os.getenv("CLAUDE_MODEL", "claude-opus-4-20250514"),
                "providerID": "anthropic",
                "mode": "primary",
                "path": {
                    "cwd": session.directory,
                    "root": session.directory
                },
                "system": [],
                "cost": 0,
                "tokens": {
                    "input": 0,
                    "output": 0,
                    "reasoning": 0,
                    "cache": {
                        "read": 0,
                        "write": 0
                    }
                }
            }
        }
    })

    # Process with Claude Agent SDK
    accumulated_text = ""
    part_id = generate_id("part")

    try:
        # Convert parts to dict for agent
        parts_dict = [part.model_dump() for part in request.parts]

        async for event in agent_manager.send_message_streaming(session_id, parts_dict):
            event_type = event.get("type")

            if event_type == "content.delta":
                text = event.get("text", "")
                accumulated_text += text

                # Send message.part.updated event with full TextPart
                await send_sse_event(session_id, {
                    "type": "message.part.updated",
                    "properties": {
                        "part": {
                            "id": part_id,
                            "type": "text",
                            "text": accumulated_text,  # Full text, not delta
                            "messageID": assistant_message_id,
                            "sessionID": session_id
                        }
                    }
                })

            elif event_type == "message.completed":
                full_text = event.get("full_text", accumulated_text)
                completed_time = int(time.time() * 1000)

                # Update assistant message with final text
                assistant_message = Message(
                    info=MessageInfo(
                        id=assistant_message_id,
                        sessionID=session_id,
                        role="assistant",
                        time=TimeInfo(
                            created=now,
                            completed=completed_time
                        )
                    ),
                    parts=[TextPart(id=part_id, type="text", text=full_text)]
                )
                storage.add_message(session_id, assistant_message)

                # Send message.updated event (message completed)
                await send_sse_event(session_id, {
                    "type": "message.updated",
                    "properties": {
                        "info": {
                            "id": assistant_message_id,
                            "sessionID": session_id,
                            "role": "assistant",
                            "time": {
                                "created": now,
                                "completed": completed_time
                            },
                            "modelID": os.getenv("CLAUDE_MODEL", "claude-opus-4-20250514"),
                            "providerID": "anthropic",
                            "mode": "primary",
                            "path": {
                                "cwd": session.directory,
                                "root": session.directory
                            },
                            "system": [],
                            "cost": 0,
                            "tokens": {
                                "input": 0,
                                "output": 0,
                                "reasoning": 0,
                                "cache": {
                                    "read": 0,
                                    "write": 0
                                }
                            }
                        }
                    }
                })

                # Return simple format (matches TUI adapter - HTTP response doesn't need all fields)
                logger.info(f"Returning assistant message: {assistant_message_id}")
                response_dict = {
                    "info": {
                        "id": assistant_message_id,
                        "sessionID": session_id,
                        "role": "assistant",
                        "time": {
                            "created": now,
                            "completed": completed_time
                        }
                    },
                    "parts": [{
                        "id": part_id,
                        "type": "text",
                        "text": full_text
                    }]
                }
                logger.info(f"Response JSON: {json.dumps(response_dict)[:200]}")
                return response_dict

            elif event_type == "error":
                error_msg = event.get("error", "Unknown error")
                logger.error(f"Error in agent: {error_msg}")
                raise HTTPException(status_code=500, detail=error_msg)

            elif event_type == "message.aborted":
                logger.info(f"Message aborted for session {session_id}")
                break

        # If we got here without completing, return partial or empty response
        completed_time = int(time.time() * 1000)
        if accumulated_text:
            logger.info(f"Returning partial message: {assistant_message_id}")
            return {
                "info": {
                    "id": assistant_message_id,
                    "sessionID": session_id,
                    "role": "assistant",
                    "time": {
                        "created": now,
                        "completed": completed_time
                    }
                },
                "parts": [{
                    "id": part_id,
                    "type": "text",
                    "text": accumulated_text
                }]
            }
        else:
            # No content received - return empty message
            logger.warning("No content received from Claude, returning empty message")
            return {
                "info": {
                    "id": assistant_message_id,
                    "sessionID": session_id,
                    "role": "assistant",
                    "time": {
                        "created": now,
                        "completed": completed_time
                    }
                },
                "parts": [{
                    "id": part_id,
                    "type": "text",
                    "text": "[No response received]"
                }]
            }

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        completed_time = int(time.time() * 1000)

        # Return error message as plain dict
        return {
            "info": {
                "id": assistant_message_id,
                "sessionID": session_id,
                "role": "assistant",
                "time": {
                    "created": now,
                    "completed": completed_time
                }
            },
            "parts": [{
                "id": part_id,
                "type": "text",
                "text": f"Error: {str(e)}"
            }]
        }


@app.post("/session/{session_id}/abort")
async def abort_session(session_id: str):
    """Abort ongoing message"""
    log_request("POST", f"/session/{session_id}/abort")

    if agent_manager:
        agent_manager.abort_session(session_id)

    # No specific abort event needed - TUI tracks completion via message.updated
    logger.info(f"Aborted session {session_id}")

    return True


@app.get("/session/{session_id}/message/{message_id}")
async def get_message(session_id: str, message_id: str):
    """Get specific message"""
    log_request("GET", f"/session/{session_id}/message/{message_id}")

    message = storage.get_message(session_id, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return message


# ============================================================================
# COMMANDS
# ============================================================================

@app.post("/session/{session_id}/command")
async def execute_command(session_id: str, request: CommandRequest):
    """Execute slash command"""
    log_request("POST", f"/session/{session_id}/command", request.model_dump())

    # For now, just echo the command
    message_id = generate_id("msg")
    now = int(time.time() * 1000)

    response_text = f"Command /{request.command} received"
    if request.arguments:
        response_text += f" with arguments: {request.arguments}"

    message = Message(
        info=MessageInfo(
            id=message_id,
            sessionID=session_id,
            role="assistant",
            time=TimeInfo(created=now, completed=now)
        ),
        parts=[TextPart(id=generate_id("part"), type="text", text=response_text)]
    )

    storage.add_message(session_id, message)
    return message


@app.get("/command")
async def list_commands():
    """List available commands"""
    log_request("GET", "/command")
    return []


# ============================================================================
# SERVER-SENT EVENTS (SSE)
# ============================================================================

@app.get("/event")
async def event_stream(request: Request, session_id: str = None):
    """SSE stream for real-time updates"""
    logger.info(f"SSE client connected (session: {session_id})")

    # Create a queue for this client and register it
    client_queue = asyncio.Queue()

    # Register queue for all active sessions to receive events
    # OpenCode TUI doesn't pass session_id in query params, so we'll
    # broadcast to all sessions using a global queue approach
    client_id = generate_id("sse_client")

    # Store this client's queue so we can send events to it
    # We'll use a special key since we don't have session_id yet
    sse_queues[client_id] = client_queue

    async def event_generator():
        try:
            # Send initial connection event
            yield {
                "event": "message",
                "data": json.dumps({
                    "type": "server.connected",
                    "properties": {}
                })
            }
            logger.info("Sent server.connected event")

            # Keep connection alive and send queued events
            while True:
                if await request.is_disconnected():
                    logger.info("SSE client disconnected")
                    break

                try:
                    # Wait for events with timeout
                    event = await asyncio.wait_for(client_queue.get(), timeout=1.0)
                    logger.info(f"Sending SSE event: {event.get('type')}")

                    yield {
                        "event": "message",
                        "data": json.dumps(event)
                    }

                except asyncio.TimeoutError:
                    # Send keepalive
                    yield {
                        "event": "ping",
                        "data": ""
                    }

        except asyncio.CancelledError:
            logger.info("SSE stream cancelled")
        finally:
            # Remove client queue on disconnect
            if client_id in sse_queues:
                del sse_queues[client_id]
            logger.info("SSE stream closed")

    return EventSourceResponse(event_generator())


# ============================================================================
# ADDITIONAL ENDPOINTS
# ============================================================================

@app.get("/project")
async def list_projects():
    """List all projects"""
    log_request("GET", "/project")
    return [await get_current_project()]


@app.patch("/config")
async def update_config(request: Request):
    """Update configuration"""
    body = await request.json()
    log_request("PATCH", "/config", body)
    return body


@app.post("/log")
async def log_entry(request: Request):
    """Handle log entries from TUI"""
    body = await request.json()
    level = body.get("level", "info").upper()
    service = body.get("service", "unknown")
    message = body.get("message", "")

    logger.info(f"TUI LOG [{level}] [{service}]: {message}")
    return True


@app.get("/mcp")
async def mcp_status():
    """MCP status"""
    log_request("GET", "/mcp")
    return {}


# ============================================================================
# TUI INTERACTION ENDPOINTS
# ============================================================================

@app.post("/tui/append-prompt")
async def tui_append_prompt(request: Request):
    """Append text to TUI prompt"""
    body = await request.json()
    logger.debug(f"TUI append: {body.get('text', '')[:50]}")
    return True


@app.post("/tui/open-help")
async def tui_open_help():
    """Open help dialog"""
    logger.debug("TUI open help")
    return True


@app.post("/tui/open-sessions")
async def tui_open_sessions():
    """Open sessions dialog"""
    logger.debug("TUI open sessions")
    return True


@app.post("/tui/open-themes")
async def tui_open_themes():
    """Open themes dialog"""
    logger.debug("TUI open themes")
    return True


@app.post("/tui/open-models")
async def tui_open_models():
    """Open models dialog"""
    logger.debug("TUI open models")
    return True


@app.post("/tui/submit-prompt")
async def tui_submit_prompt():
    """Submit the current prompt"""
    logger.debug("TUI submit prompt")
    return True


@app.post("/tui/clear-prompt")
async def tui_clear_prompt():
    """Clear the prompt input"""
    logger.debug("TUI clear prompt")
    return True


@app.post("/tui/execute-command")
async def tui_execute_command(request: Request):
    """Execute a TUI command"""
    body = await request.json()
    logger.debug(f"TUI execute: {body.get('command')}")
    return True


@app.post("/tui/show-toast")
async def tui_show_toast(request: Request):
    """Show toast notification"""
    body = await request.json()
    logger.debug(f"TUI toast [{body.get('variant', 'info')}]: {body.get('message')}")
    return True


@app.get("/tui/control/next")
async def tui_control_next():
    """Get next TUI control request (polling endpoint)"""
    # This is a long-polling endpoint - return empty for now
    await asyncio.sleep(0.1)
    return {}


@app.post("/tui/control/response")
async def tui_control_response(request: Request):
    """Send response to TUI control request"""
    body = await request.json()
    logger.debug(f"TUI control response: {body}")
    return True


# ============================================================================
# ADDITIONAL SESSION ENDPOINTS
# ============================================================================

@app.get("/session/{session_id}/children")
async def get_session_children(session_id: str):
    """Get child sessions"""
    log_request("GET", f"/session/{session_id}/children")
    return []


@app.get("/session/{session_id}/todo")
async def get_session_todos(session_id: str):
    """Get session todos"""
    log_request("GET", f"/session/{session_id}/todo")
    return []


@app.post("/session/{session_id}/init")
async def init_session(session_id: str, request: Request):
    """Initialize session"""
    body = await request.json()
    log_request("POST", f"/session/{session_id}/init", body)
    return True


@app.post("/session/{session_id}/fork")
async def fork_session(session_id: str, request: Request):
    """Fork session"""
    body = await request.json()
    log_request("POST", f"/session/{session_id}/fork", body)
    return {}


@app.post("/session/{session_id}/share")
async def share_session(session_id: str):
    """Share session"""
    log_request("POST", f"/session/{session_id}/share")
    return {}


@app.delete("/session/{session_id}/share")
async def unshare_session(session_id: str):
    """Unshare session"""
    log_request("DELETE", f"/session/{session_id}/share")
    return True


@app.post("/session/{session_id}/summarize")
async def summarize_session(session_id: str):
    """Summarize session"""
    log_request("POST", f"/session/{session_id}/summarize")
    return {}


@app.post("/session/{session_id}/revert")
async def revert_session(session_id: str, request: Request):
    """Revert session"""
    body = await request.json()
    log_request("POST", f"/session/{session_id}/revert", body)
    return True


@app.post("/session/{session_id}/unrevert")
async def unrevert_session(session_id: str):
    """Unrevert session"""
    log_request("POST", f"/session/{session_id}/unrevert")
    return True


# Catch-all for unimplemented endpoints
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def catch_all(path: str, request: Request):
    """Handle unimplemented endpoints"""
    logger.warning(f"Unimplemented endpoint: {request.method} /{path}")
    return {}


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the server"""
    import uvicorn

    host = os.getenv("OPENCODE_HOST", "127.0.0.1")
    port = int(os.getenv("OPENCODE_PORT", "3000"))

    print("\n" + "=" * 80)
    print("OpenCode Claude Agent Adapter Starting...")
    print("=" * 80)
    print(f"\nServer: http://{host}:{port}")
    print(f"Model: {os.getenv('CLAUDE_MODEL', 'claude-opus-4-20250514')}")
    print("\nTo connect OpenCode TUI:")
    print(f"  OPENCODE_SERVER=http://{host}:{port} <path-to-tui-binary>")
    print("\n" + "=" * 80 + "\n")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
