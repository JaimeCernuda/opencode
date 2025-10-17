"""Message format translation between SDK and TUI."""

from datetime import datetime
from typing import Any, Dict, List

import structlog

from claude_agent_sdk import (
    AssistantMessage,
    UserMessage,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    ToolResultBlock,
)

from ..session.models import MessagePart, MessageRecord
from ..logging.config import trace_function


logger = structlog.get_logger(__name__)


@trace_function
def sdk_message_to_tui_parts(message: AssistantMessage | UserMessage) -> List[Dict[str, Any]]:
    """Convert SDK message to TUI parts format."""
    parts = []
    message_type = type(message).__name__
    logger.debug("sdk_message_to_tui_parts_start", message_type=message_type)

    if isinstance(message, UserMessage):
        # Simple text for user messages
        if isinstance(message.content, str):
            parts.append({
                "id": f"part_{datetime.now().timestamp()}",
                "type": "text",
                "text": message.content,
            })
            logger.debug("sdk_message_to_tui_parts_user_text", text_length=len(message.content))
        else:
            # List of content blocks
            for idx, block in enumerate(message.content):
                part_id = f"part_{datetime.now().timestamp()}_{idx}"
                if isinstance(block, TextBlock):
                    parts.append({
                        "id": part_id,
                        "type": "text",
                        "text": block.text,
                    })
                    logger.debug("sdk_message_to_tui_parts_user_block", idx=idx, block_type="text")

    elif isinstance(message, AssistantMessage):
        logger.debug("sdk_message_to_tui_parts_assistant", block_count=len(message.content))

        for idx, block in enumerate(message.content):
            part_id = f"part_{datetime.now().timestamp()}_{idx}"
            block_type = type(block).__name__

            if isinstance(block, TextBlock):
                parts.append({
                    "id": part_id,
                    "type": "text",
                    "text": block.text,
                })
                logger.debug("sdk_message_to_tui_parts_text_block", idx=idx, text_preview=block.text[:100])

            elif isinstance(block, ThinkingBlock):
                parts.append({
                    "id": part_id,
                    "type": "thinking",
                    "thinking": block.thinking,
                    "signature": block.signature,
                })
                logger.debug("sdk_message_to_tui_parts_thinking_block", idx=idx, thinking_preview=block.thinking[:100])

            elif isinstance(block, ToolUseBlock):
                parts.append({
                    "id": part_id,
                    "type": "tool",
                    "tool": block.name,
                    "state": {
                        "status": "pending",
                        "title": block.name,
                        "input": block.input,
                    }
                })
                logger.debug("sdk_message_to_tui_parts_tool_use_block", idx=idx, tool_name=block.name)

            elif isinstance(block, ToolResultBlock):
                parts.append({
                    "id": part_id,
                    "type": "tool_result",
                    "tool_use_id": block.tool_use_id,
                    "content": block.content,
                    "is_error": block.is_error,
                })
                logger.debug("sdk_message_to_tui_parts_tool_result_block", idx=idx, is_error=block.is_error)
            else:
                logger.debug("sdk_message_to_tui_parts_unknown_block", idx=idx, block_type=block_type)

    logger.debug("sdk_message_to_tui_parts_complete", part_count=len(parts))
    return parts


@trace_function
def create_tui_message(
    message_id: str,
    session_id: str,
    role: str,
    parts: List[Dict[str, Any]],
    created_at: int | None = None,
    completed_at: int | None = None,
) -> Dict[str, Any]:
    """Create a TUI-format message."""
    logger.debug("create_tui_message_start", message_id=message_id, session_id=session_id, role=role, part_count=len(parts))

    created_at = created_at or int(datetime.now().timestamp() * 1000)

    time_info = {"created": created_at}
    if completed_at:
        time_info["completed"] = completed_at
        logger.debug("create_tui_message_completed", message_id=message_id, duration_ms=completed_at - created_at)

    result = {
        "info": {
            "id": message_id,
            "sessionID": session_id,
            "role": role,
            "time": time_info,
        },
        "parts": parts,
    }

    logger.debug("create_tui_message_complete", message_id=message_id)
    return result
