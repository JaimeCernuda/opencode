"""Unit tests for message translation."""

from claude_agent_sdk import AssistantMessage, TextBlock, ToolUseBlock
from opencode_tui_adapter.utils.translation import sdk_message_to_tui_parts, create_tui_message


def test_text_block_translation():
    """Test TextBlock translation."""
    message = AssistantMessage(
        content=[TextBlock(text="Hello, world!")],
        model="claude-3-5-sonnet"
    )

    parts = sdk_message_to_tui_parts(message)

    assert len(parts) == 1
    assert parts[0]["type"] == "text"
    assert parts[0]["text"] == "Hello, world!"


def test_tool_use_block_translation():
    """Test ToolUseBlock translation."""
    message = AssistantMessage(
        content=[
            ToolUseBlock(
                id="tool_123",
                name="Read",
                input={"file_path": "/test.txt"}
            )
        ],
        model="claude-3-5-sonnet"
    )

    parts = sdk_message_to_tui_parts(message)

    assert len(parts) == 1
    assert parts[0]["type"] == "tool"
    assert parts[0]["tool"] == "Read"
    assert parts[0]["state"]["input"]["file_path"] == "/test.txt"


def test_multiple_blocks_translation():
    """Test multiple content blocks translation."""
    message = AssistantMessage(
        content=[
            TextBlock(text="Let me read the file."),
            ToolUseBlock(
                id="tool_456",
                name="Read",
                input={"file_path": "/test.txt"}
            ),
            TextBlock(text="Done reading.")
        ],
        model="claude-3-5-sonnet"
    )

    parts = sdk_message_to_tui_parts(message)

    assert len(parts) == 3
    assert parts[0]["type"] == "text"
    assert parts[0]["text"] == "Let me read the file."
    assert parts[1]["type"] == "tool"
    assert parts[2]["type"] == "text"
    assert parts[2]["text"] == "Done reading."


def test_create_tui_message():
    """Test TUI message creation."""
    parts = [
        {"id": "part_1", "type": "text", "text": "Hello"}
    ]

    message = create_tui_message(
        message_id="msg_123",
        session_id="session_456",
        role="assistant",
        parts=parts,
        created_at=1000000,
        completed_at=1001000
    )

    assert message["info"]["id"] == "msg_123"
    assert message["info"]["sessionID"] == "session_456"
    assert message["info"]["role"] == "assistant"
    assert message["info"]["time"]["created"] == 1000000
    assert message["info"]["time"]["completed"] == 1001000
    assert message["parts"] == parts
