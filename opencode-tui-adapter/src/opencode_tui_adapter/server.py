"""
OpenCode TUI Adapter - Main Server
Backend server that connects OpenCode TUI to Claude Agent SDK
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette import EventSourceResponse
import structlog
import uvicorn

from .config import get_config, get_config_file_path
from .events.bus import get_event_bus
from .events.models import Event
from .logging import setup_logging
from .logging.config import trace_function
from .session import get_session_manager
from .utils.translation import sdk_message_to_tui_parts, create_tui_message
from .utils.id_generator import generate_id


# Initialize logging
config = get_config()
setup_logging(config.log_level)
logger = structlog.get_logger(__name__)

# Create FastAPI app
app = FastAPI(title="OpenCode TUI Adapter", version="0.1.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get global instances
session_manager = get_session_manager()
event_bus = get_event_bus()


# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body_bytes = await request.body()
            if body_bytes:
                body = json.loads(body_bytes.decode())
                # Recreate request for downstream handlers
                async def receive():
                    return {"type": "http.request", "body": body_bytes}
                request._receive = receive
        except Exception as e:
            logger.warning("request_body_parse_error", error=str(e))

    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        query=dict(request.query_params),
        body_preview=str(body)[:200] if body else None,
    )

    response = await call_next(request)
    return response


# ============================================================================
# CORE ENDPOINTS - Phase 1
# ============================================================================

@app.get("/project/current")
@trace_function
async def get_current_project():
    """Return current project info."""
    result = {
        "id": config.project.id,
        "worktree": config.project.worktree,
        "vcs": config.project.vcs,
        "initialized": config.project.initialized,
    }
    logger.debug("get_current_project_result", result=result)
    return result


@app.get("/agent")
@trace_function
async def list_agents():
    """Return available agents."""
    agents = [
        {
            "name": agent.name,
            "description": agent.description,
            "mode": "primary",
            "model": {
                "providerID": "anthropic",
                "modelID": agent.model,
            }
        }
        for agent in config.agents
    ]
    logger.debug("list_agents_result", agent_count=len(agents))
    return agents


@app.get("/path")
@trace_function
async def get_paths():
    """Return filesystem paths."""
    paths = {
        "state": config.state_path,
        "config": config.config_path,
        "worktree": config.project.worktree,
        "directory": config.project.worktree,
    }
    logger.debug("get_paths_result", paths=paths)
    return paths


@app.get("/config")
@trace_function
async def get_config_endpoint():
    """Return configuration."""
    config_data = {
        "theme": config.theme,
        "share": "disabled",
        "model": "",
        "keybinds": {
            "leader": "ctrl+x"
        },
        "tui": {
            "scrollSpeed": 3
        }
    }
    logger.debug("get_config_result", config=config_data)
    return config_data


@app.patch("/config")
@trace_function
async def update_config(request: Request):
    """Update configuration settings."""
    body = await request.json()
    logger.info("update_config_request", updates=body)

    try:
        # Store old values for logging
        old_theme = config.theme
        old_log_level = config.log_level

        # Update configuration
        config.update_from_dict(body)

        # Log changes
        logger.info(
            "config_updated",
            theme_changed=old_theme != config.theme,
            new_theme=config.theme if old_theme != config.theme else None,
            log_level_changed=old_log_level != config.log_level,
            new_log_level=config.log_level if old_log_level != config.log_level else None,
        )

        # Persist configuration to disk
        config_file_path = get_config_file_path()
        config.save_to_yaml(config_file_path)
        logger.debug("config_saved_to_file", path=str(config_file_path))

        # Broadcast config update event
        await event_bus.broadcast(Event(
            type="config.updated",
            properties={
                "config": {
                    "theme": config.theme,
                    "log_level": config.log_level,
                }
            }
        ))

        # Return updated config
        config_data = {
            "theme": config.theme,
            "share": "disabled",
            "model": "",
            "keybinds": {
                "leader": "ctrl+x"
            },
            "tui": {
                "scrollSpeed": 3
            }
        }
        logger.debug("update_config_success", config=config_data)
        return config_data

    except ValueError as e:
        logger.warning("update_config_invalid_value", error=str(e))
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )
    except Exception as e:
        logger.error("update_config_error", error=str(e), exception_type=type(e).__name__)
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to update configuration: {str(e)}"}
        )


@app.get("/config/providers")
@trace_function
async def list_providers():
    """Return AI providers and models."""
    logger.debug("list_providers_start")

    providers_data = []
    default_models = {}

    for provider in config.providers:
        models_dict = {
            model_id: {
                "id": model.id,
                "name": model.name,
            }
            for model_id, model in provider.models.items()
        }

        providers_data.append({
            "id": provider.id,
            "name": provider.name,
            "models": models_dict,
        })

        # Set default model for provider
        if provider.models:
            first_model_id = next(iter(provider.models.keys()))
            default_models[provider.id] = first_model_id

    result = {
        "providers": providers_data,
        "default": default_models,
    }
    logger.debug("list_providers_result", provider_count=len(providers_data))
    return result


# ============================================================================
# SESSION ENDPOINTS
# ============================================================================

@app.post("/session")
@trace_function
async def create_session(request: Request):
    """Create a new session."""
    body = {}
    try:
        if request.headers.get("content-type") == "application/json":
            body = await request.json()
    except:
        pass

    logger.debug("create_session_request", title=body.get("title"), parent_id=body.get("parentID"))

    title = body.get("title")
    parent_id = body.get("parentID")

    session = await session_manager.create_session(
        title=title,
        parent_id=parent_id,
    )

    logger.debug("create_session_success", session_id=session.id, title=session.title)

    # Broadcast session created event
    await event_bus.broadcast(Event(
        type="session.updated",
        properties={"session": session.to_dict()}
    ))

    return session.to_dict()


@app.get("/session")
@trace_function
async def list_sessions():
    """List all sessions."""
    sessions = session_manager.list_sessions()
    logger.debug("list_sessions_result", session_count=len(sessions))
    return [session.to_dict() for session in sessions]


@app.get("/session/{session_id}")
@trace_function
async def get_session(session_id: str):
    """Get a specific session."""
    logger.debug("get_session_request", session_id=session_id)

    session = session_manager.get_session(session_id)
    if not session:
        logger.debug("get_session_not_found", session_id=session_id)
        return JSONResponse(
            status_code=404,
            content={"error": f"Session {session_id} not found"}
        )

    logger.debug("get_session_success", session_id=session_id, title=session.title)
    return session.to_dict()


@app.delete("/session/{session_id}")
@trace_function
async def delete_session(session_id: str):
    """Delete a session."""
    logger.debug("delete_session_request", session_id=session_id)

    success = await session_manager.delete_session(session_id)
    if not success:
        logger.debug("delete_session_not_found", session_id=session_id)
        return JSONResponse(
            status_code=404,
            content={"error": f"Session {session_id} not found"}
        )

    logger.debug("delete_session_success", session_id=session_id)
    return True


@app.patch("/session/{session_id}")
@trace_function
async def update_session(session_id: str, request: Request):
    """Update session metadata."""
    body = await request.json()
    logger.debug("update_session_request", session_id=session_id, updates=body)

    session = session_manager.update_session_metadata(session_id, **body)
    if not session:
        logger.debug("update_session_not_found", session_id=session_id)
        return JSONResponse(
            status_code=404,
            content={"error": f"Session {session_id} not found"}
        )

    logger.debug("update_session_success", session_id=session_id, title=session.title)

    # Broadcast session updated event
    await event_bus.broadcast(Event(
        type="session.updated",
        properties={"session": session.to_dict()}
    ))

    return session.to_dict()


@app.post("/session/{session_id}/abort")
@trace_function
async def abort_session(session_id: str):
    """Abort a running session operation."""
    logger.debug("abort_session_request", session_id=session_id)

    success = await session_manager.abort_session(session_id)
    logger.debug("abort_session_result", session_id=session_id, success=success)
    return success


# ============================================================================
# MESSAGE ENDPOINTS
# ============================================================================

@app.get("/session/{session_id}/message")
@trace_function
async def list_messages(session_id: str):
    """List all messages in a session."""
    logger.debug("list_messages_request", session_id=session_id)

    session = session_manager.get_session(session_id)
    if not session:
        logger.debug("list_messages_session_not_found", session_id=session_id)
        return JSONResponse(
            status_code=404,
            content={"error": f"Session {session_id} not found"}
        )

    # Convert message records to TUI format
    messages = []
    for msg in session.messages:
        messages.append(create_tui_message(
            message_id=msg.id,
            session_id=msg.session_id,
            role=msg.role,
            parts=[part.data for part in msg.parts],
            created_at=msg.created_at,
            completed_at=msg.completed_at,
        ))

    logger.debug("list_messages_result", session_id=session_id, message_count=len(messages))
    return messages


@app.post("/session/{session_id}/message")
@trace_function
async def send_message(session_id: str, request: Request):
    """Send a message to the session."""
    body = await request.json()

    logger.info(
        "send_message_request",
        session_id=session_id,
        message_id=body.get("messageID"),
        agent=body.get("agent"),
    )

    session = session_manager.get_session(session_id)
    if not session:
        logger.debug("send_message_session_not_found", session_id=session_id)
        return JSONResponse(
            status_code=404,
            content={"error": f"Session {session_id} not found"}
        )

    if not session.client:
        logger.error("send_message_client_not_initialized", session_id=session_id)
        return JSONResponse(
            status_code=500,
            content={"error": "Session client not initialized"}
        )

    # Extract prompt from parts
    parts = body.get("parts", [])
    prompt_text = ""
    for part in parts:
        if part.get("type") == "text":
            prompt_text += part.get("text", "")

    logger.debug("send_message_prompt", session_id=session_id, prompt_preview=prompt_text[:200])

    message_id = body.get("messageID", generate_id("msg"))

    # Send query to Claude
    logger.debug("send_message_querying_claude", session_id=session_id, message_id=message_id)
    await session.client.query(prompt_text)

    # Collect response
    response_parts = []
    try:
        logger.debug("send_message_receiving_response", session_id=session_id)
        async for message in session.client.receive_response():
            # Convert SDK message to TUI parts
            parts = sdk_message_to_tui_parts(message)
            response_parts.extend(parts)
            logger.debug("send_message_received_parts", session_id=session_id, part_count=len(parts))

            # Broadcast message part updates
            for part in parts:
                await event_bus.broadcast(Event(
                    type="message.part.updated",
                    properties={
                        "sessionID": session_id,
                        "messageID": message_id,
                        "part": part,
                    }
                ))
    except Exception as e:
        logger.error("message_receive_error", session_id=session_id, error=str(e), exception_type=type(e).__name__)
        # Return error response
        return JSONResponse(
            status_code=500,
            content={"error": f"Error receiving message: {str(e)}"}
        )

    # Create final response
    completed_at = int(datetime.now().timestamp() * 1000)

    response = create_tui_message(
        message_id=message_id,
        session_id=session_id,
        role="assistant",
        parts=response_parts,
        completed_at=completed_at,
    )

    logger.info("send_message_complete", session_id=session_id, message_id=message_id, part_count=len(response_parts))

    # Broadcast final message update
    await event_bus.broadcast(Event(
        type="message.updated",
        properties={
            "sessionID": session_id,
            "message": response,
        }
    ))

    return response


# ============================================================================
# SERVER-SENT EVENTS (SSE)
# ============================================================================

@app.get("/event")
@trace_function
async def event_stream(request: Request):
    """SSE stream for real-time updates."""
    logger.info("sse_stream_connected")

    queue_id, queue = event_bus.subscribe()
    logger.debug("sse_subscriber_created", queue_id=queue_id)

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
            logger.debug("sse_sent_event", event_type="server.connected", queue_id=queue_id)

            # Stream events from queue
            while True:
                if await request.is_disconnected():
                    logger.info("sse_stream_disconnected", queue_id=queue_id)
                    break

                try:
                    # Wait for event with timeout
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield {
                        "event": "message",
                        "data": json.dumps(event.to_dict())
                    }
                    logger.debug("sse_sent_event", event_type=event.type, queue_id=queue_id)
                except asyncio.TimeoutError:
                    # Send keep-alive comment
                    yield {"comment": "keep-alive"}
                    logger.debug("sse_sent_keepalive", queue_id=queue_id)
                    continue

        except asyncio.CancelledError:
            logger.info("sse_stream_cancelled", queue_id=queue_id)

        finally:
            logger.debug("sse_unsubscribing", queue_id=queue_id)
            event_bus.unsubscribe(queue_id)

    return EventSourceResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ============================================================================
# STUB ENDPOINTS (Not Yet Implemented)
# ============================================================================

@app.get("/command")
@trace_function
async def list_commands():
    """List custom commands - NOT IMPLEMENTED."""
    logger.warning("list_commands_not_implemented")
    return JSONResponse(
        status_code=501,
        content={
            "error": "Not Implemented",
            "message": "Custom slash commands are not yet implemented"
        }
    )


@app.post("/log")
@trace_function
async def log_entry(request: Request):
    """Handle log entry from TUI."""
    body = await request.json()
    level = body.get("level", "info")
    service = body.get("service", "tui")
    message = body.get("message", "")
    extra = body.get("extra", {})

    logger.debug("log_entry_received", level=level, service=service, message_preview=message[:200])

    # Map TUI log levels to Python logging levels
    log_method = {
        "debug": logger.debug,
        "info": logger.info,
        "warn": logger.warning,
        "error": logger.error,
    }.get(level.lower(), logger.info)

    log_method(
        "tui_log",
        service=service,
        message=message,
        **extra
    )

    return True


@app.get("/mcp")
@trace_function
async def mcp_status():
    """Get MCP status - NOT IMPLEMENTED."""
    logger.warning("mcp_status_not_implemented")
    return JSONResponse(
        status_code=501,
        content={
            "error": "Not Implemented",
            "message": "MCP server status endpoints are not yet implemented"
        }
    )


# ============================================================================
# TUI CONTROL ENDPOINTS (Not Implemented - bidirectional TUI communication)
# ============================================================================

@app.post("/tui/append-prompt")
@trace_function
async def tui_append_prompt(request: Request):
    """Append text to TUI prompt - NOT IMPLEMENTED."""
    logger.warning("tui_append_prompt_not_implemented")
    return JSONResponse(
        status_code=501,
        content={
            "error": "Not Implemented",
            "message": "TUI control endpoints are not yet implemented"
        }
    )


@app.post("/tui/open-help")
@trace_function
async def tui_open_help():
    """Open help dialog in TUI - NOT IMPLEMENTED."""
    logger.warning("tui_open_help_not_implemented")
    return JSONResponse(
        status_code=501,
        content={
            "error": "Not Implemented",
            "message": "TUI control endpoints are not yet implemented"
        }
    )


@app.post("/tui/open-sessions")
@trace_function
async def tui_open_sessions():
    """Open sessions dialog in TUI - NOT IMPLEMENTED."""
    logger.warning("tui_open_sessions_not_implemented")
    return JSONResponse(
        status_code=501,
        content={
            "error": "Not Implemented",
            "message": "TUI control endpoints are not yet implemented"
        }
    )


@app.post("/tui/open-themes")
@trace_function
async def tui_open_themes():
    """Open themes dialog in TUI - NOT IMPLEMENTED."""
    logger.warning("tui_open_themes_not_implemented")
    return JSONResponse(
        status_code=501,
        content={
            "error": "Not Implemented",
            "message": "TUI control endpoints are not yet implemented"
        }
    )


@app.post("/tui/open-models")
@trace_function
async def tui_open_models():
    """Open models dialog in TUI - NOT IMPLEMENTED."""
    logger.warning("tui_open_models_not_implemented")
    return JSONResponse(
        status_code=501,
        content={
            "error": "Not Implemented",
            "message": "TUI control endpoints are not yet implemented"
        }
    )


@app.post("/tui/submit-prompt")
@trace_function
async def tui_submit_prompt():
    """Submit prompt in TUI - NOT IMPLEMENTED."""
    logger.warning("tui_submit_prompt_not_implemented")
    return JSONResponse(
        status_code=501,
        content={
            "error": "Not Implemented",
            "message": "TUI control endpoints are not yet implemented"
        }
    )


@app.post("/tui/clear-prompt")
@trace_function
async def tui_clear_prompt():
    """Clear prompt in TUI - NOT IMPLEMENTED."""
    logger.warning("tui_clear_prompt_not_implemented")
    return JSONResponse(
        status_code=501,
        content={
            "error": "Not Implemented",
            "message": "TUI control endpoints are not yet implemented"
        }
    )


@app.post("/tui/execute-command")
@trace_function
async def tui_execute_command(request: Request):
    """Execute TUI command - NOT IMPLEMENTED."""
    logger.warning("tui_execute_command_not_implemented")
    return JSONResponse(
        status_code=501,
        content={
            "error": "Not Implemented",
            "message": "TUI control endpoints are not yet implemented"
        }
    )


@app.post("/tui/show-toast")
@trace_function
async def tui_show_toast(request: Request):
    """Show toast notification in TUI - NOT IMPLEMENTED."""
    logger.warning("tui_show_toast_not_implemented")
    return JSONResponse(
        status_code=501,
        content={
            "error": "Not Implemented",
            "message": "TUI control endpoints are not yet implemented"
        }
    )


@app.get("/tui/control/next")
@trace_function
async def tui_control_next():
    """Get next TUI control request - NOT IMPLEMENTED."""
    logger.warning("tui_control_next_not_implemented")
    return JSONResponse(
        status_code=501,
        content={
            "error": "Not Implemented",
            "message": "TUI control endpoints are not yet implemented"
        }
    )


@app.post("/tui/control/response")
@trace_function
async def tui_control_response(request: Request):
    """Send response to TUI control request - NOT IMPLEMENTED."""
    logger.warning("tui_control_response_not_implemented")
    return JSONResponse(
        status_code=501,
        content={
            "error": "Not Implemented",
            "message": "TUI control endpoints are not yet implemented"
        }
    )


# ============================================================================
# DOCUMENTATION ENDPOINT
# ============================================================================

@app.get("/doc")
@trace_function
async def get_documentation():
    """Return OpenAPI documentation."""
    logger.debug("get_documentation")

    # Return basic API documentation
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "OpenCode TUI Adapter API",
            "version": "0.1.0",
            "description": "Backend adapter that connects OpenCode TUI to Claude Agent SDK"
        },
        "servers": [
            {
                "url": f"http://{config.host}:{config.port}",
                "description": "Local development server"
            }
        ],
        "paths": {
            "/project/current": {
                "get": {
                    "summary": "Get current project",
                    "responses": {"200": {"description": "Project information"}}
                }
            },
            "/agent": {
                "get": {
                    "summary": "List available agents",
                    "responses": {"200": {"description": "Array of agents"}}
                }
            },
            "/config": {
                "get": {
                    "summary": "Get configuration",
                    "responses": {"200": {"description": "Configuration object"}}
                },
                "patch": {
                    "summary": "Update configuration",
                    "responses": {"200": {"description": "Updated configuration"}}
                }
            },
            "/session": {
                "get": {
                    "summary": "List all sessions",
                    "responses": {"200": {"description": "Array of sessions"}}
                },
                "post": {
                    "summary": "Create new session",
                    "responses": {"200": {"description": "Created session"}}
                }
            },
            "/event": {
                "get": {
                    "summary": "Server-Sent Events stream",
                    "responses": {"200": {"description": "SSE stream"}}
                }
            }
        }
    }


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the server."""
    logger.info(
        "server_starting",
        host=config.host,
        port=config.port,
        log_level=config.log_level,
    )

    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level=config.log_level.lower(),
    )


if __name__ == "__main__":
    main()
