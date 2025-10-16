"""Claude Agent SDK integration - Simple query() approach"""

import os
from typing import AsyncGenerator, Dict, Any, List
from claude_agent_sdk import query
import logging

logger = logging.getLogger(__name__)


class ClaudeAgentManager:
    """Manages Claude Agent SDK conversations using simple query() function"""

    def __init__(self):
        # Claude Agent SDK's query() function handles everything automatically
        # No need for manual client management or API key validation

        self.model = os.getenv("CLAUDE_MODEL", "claude-opus-4-20250514")
        self.abort_flags: Dict[str, bool] = {}

        logger.info(f"Claude Agent Manager initialized")
        logger.info(f"Using Claude Agent SDK query() function")
        logger.info(f"Model: {self.model}")

    def _convert_opencode_to_prompt(self, parts: List[Dict[str, Any]]) -> str:
        """Convert OpenCode message parts to a prompt string"""
        prompt_parts = []

        for part in parts:
            part_type = part.get("type")

            if part_type == "text":
                prompt_parts.append(part.get("text", ""))
            elif part_type == "file":
                # For files, mention the file path
                file_path = part.get("path", "")
                prompt_parts.append(f"[File reference: {file_path}]")
            # Handle other part types as needed

        return "\n".join(prompt_parts)

    async def send_message_streaming(
        self,
        session_id: str,
        parts: List[Dict[str, Any]],
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Send message using Claude Agent SDK's simple query() function"""

        # Reset abort flag
        self.abort_flags[session_id] = False

        # Convert OpenCode parts to prompt
        prompt = self._convert_opencode_to_prompt(parts)

        logger.info(f"Sending query to Claude Agent SDK for session {session_id}")
        logger.debug(f"Prompt: {prompt}")

        try:
            # Use the simple query() function - it handles everything!
            accumulated_text = ""
            result_message_received = False

            logger.info(f"Starting query() streaming for prompt: {prompt[:50]}...")

            async for message in query(prompt=prompt):
                # Get message type name
                message_type = type(message).__name__
                logger.info(f"Received message type: {message_type}")
                logger.debug(f"Message object: {message}")

                # Check for abort
                if self.abort_flags.get(session_id, False):
                    logger.info(f"Message aborted for session {session_id}")
                    yield {
                        "type": "message.aborted",
                        "session_id": session_id
                    }
                    # Don't break - let the generator complete naturally
                    result_message_received = True
                    continue

                # Handle SystemMessage (initialization) - skip it
                if message_type == 'SystemMessage':
                    logger.info("Skipping SystemMessage (initialization)")
                    continue

                # Handle ResultMessage (summary) - this is the final message
                if message_type == 'ResultMessage':
                    if hasattr(message, 'is_error') and message.is_error:
                        error_text = str(message.result) if hasattr(message, 'result') else "Unknown error"
                        logger.error(f"SDK returned error in ResultMessage: {error_text}")
                        yield {
                            "type": "error",
                            "error": error_text
                        }
                    else:
                        logger.info(f"ResultMessage: {message.result if hasattr(message, 'result') else 'No result'}")
                    # Mark that we received the result message
                    result_message_received = True
                    # Don't break - let the async generator complete naturally
                    continue

                # Skip processing if we already got the result
                if result_message_received:
                    continue

                # Handle AssistantMessage - extract text from content blocks
                if message_type == 'AssistantMessage':
                    if hasattr(message, 'content'):
                        logger.info(f"AssistantMessage has content with {len(message.content)} blocks")

                        for block in message.content:
                            block_type = type(block).__name__
                            logger.info(f"Processing block type: {block_type}")

                            # Check if it's a TextBlock
                            if hasattr(block, 'text'):
                                text = block.text
                                logger.info(f"Extracted text (length: {len(text)}): {text[:100]}")
                                accumulated_text += text

                                # Yield text delta
                                yield {
                                    "type": "content.delta",
                                    "text": text,
                                }
                            elif hasattr(block, 'type') and block.type == 'tool_use':
                                # Tool use block
                                logger.info(f"Tool use: {block.name}")
                            else:
                                logger.warning(f"Unknown block type: {block_type}, attributes: {dir(block)}")
                    else:
                        logger.warning(f"AssistantMessage has no 'content' attribute")
                    continue

                # Unknown message type
                logger.warning(f"Unknown message type: {message_type}, attributes: {dir(message)}")

            logger.info(f"Finished streaming. Total text length: {len(accumulated_text)}")

            # Yield completion event
            if accumulated_text and not self.abort_flags.get(session_id, False):
                yield {
                    "type": "message.completed",
                    "full_text": accumulated_text
                }
            elif not accumulated_text:
                logger.warning("No text was accumulated from the query!")

        except Exception as e:
            logger.error(f"Error in Claude Agent SDK query(): {e}", exc_info=True)
            yield {
                "type": "error",
                "error": str(e)
            }

    def abort_session(self, session_id: str):
        """Abort ongoing message for session"""
        logger.info(f"Aborting session {session_id}")
        self.abort_flags[session_id] = True

    async def clear_session(self, session_id: str):
        """Clear session data"""
        # With simple query(), we don't need to manage clients
        if session_id in self.abort_flags:
            del self.abort_flags[session_id]

        logger.info(f"Cleared session {session_id}")
