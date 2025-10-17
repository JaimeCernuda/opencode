# Claude Agent SDK for Python - Documentation

> Comprehensive documentation compiled from the official Claude Agent SDK Python repository and API documentation.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [API Reference](#api-reference)
- [Advanced Features](#advanced-features)
- [Examples](#examples)
- [Migration Guide](#migration-guide)

---

## Overview

The Claude Agent SDK for Python enables programmatic interaction with Claude Code, providing both simple one-off queries and sophisticated multi-turn conversations with tool usage, custom tools, and hooks.

**Key Features:**
- 🔄 Continuous conversation sessions with context retention
- 🛠️ Built-in tools (Bash, Read, Write, Edit, Grep, Glob, etc.)
- 🔌 Custom tool creation with in-process MCP servers
- 🪝 Hooks for intercepting and modifying agent behavior
- ⚡ Streaming input/output support
- 🎛️ Fine-grained permission control
- 🔍 Real-time progress monitoring

---

## Installation

### Prerequisites

- **Python:** 3.10 or higher
- **Node.js:** Required for Claude Code CLI
- **Claude Code:** Version 2.0.0 or higher

### Install the SDK

```bash
pip install claude-agent-sdk
```

### Install Claude Code CLI

```bash
npm install -g @anthropic-ai/claude-code
```

---

## Quick Start

### Simple Query

```python
import asyncio
from claude_agent_sdk import query

async def main():
    async for message in query(prompt="What is 2 + 2?"):
        print(message)

asyncio.run(main())
```

### Query with Options

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

async def create_file():
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Bash"],
        permission_mode='acceptEdits',
        cwd="/path/to/project"
    )
    
    async for message in query(
        prompt="Create a hello.py file",
        options=options
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)

asyncio.run(create_file())
```

---

## Core Concepts

### Choosing Between `query()` and `ClaudeSDKClient`

The SDK provides two approaches for interacting with Claude:

#### Quick Comparison

| Feature | `query()` | `ClaudeSDKClient` |
|---------|-----------|-------------------|
| **Session** | Creates new session each time | Reuses same session |
| **Conversation** | Single exchange | Multiple exchanges in same context |
| **Connection** | Managed automatically | Manual control |
| **Streaming Input** | ✅ Supported | ✅ Supported |
| **Interrupts** | ❌ Not supported | ✅ Supported |
| **Hooks** | ❌ Not supported | ✅ Supported |
| **Custom Tools** | ❌ Not supported | ✅ Supported |
| **Continue Chat** | ❌ New session each time | ✅ Maintains conversation |
| **Use Case** | One-off tasks | Continuous conversations |

#### When to Use `query()`

Best for:
- One-off questions where you don't need conversation history
- Independent tasks that don't require context from previous exchanges
- Simple automation scripts
- When you want a fresh start each time

#### When to Use `ClaudeSDKClient`

Best for:
- Continuing conversations - when you need Claude to remember context
- Follow-up questions - building on previous responses
- Interactive applications - chat interfaces, REPLs
- Response-driven logic - when next action depends on Claude's response
- Session control - managing conversation lifecycle explicitly
- Using custom tools or hooks

---

## API Reference

### Functions

#### `query()`

Creates a new session for each interaction with Claude Code. Returns an async iterator that yields messages as they arrive.

```python
async def query(
    *,
    prompt: str | AsyncIterable[dict[str, Any]],
    options: ClaudeAgentOptions | None = None
) -> AsyncIterator[Message]
```

**Parameters:**
- `prompt` (str | AsyncIterable[dict]): The input prompt as a string or async iterable for streaming mode
- `options` (ClaudeAgentOptions | None): Optional configuration object

**Returns:** `AsyncIterator[Message]` - Yields messages from the conversation

**Example:**
```python
options = ClaudeAgentOptions(
    system_prompt="You are an expert Python developer",
    permission_mode='acceptEdits',
    cwd="/home/user/project"
)

async for message in query(
    prompt="Create a Python web server",
    options=options
):
    print(message)
```

#### `tool()`

Decorator for defining MCP tools with type safety.

```python
def tool(
    name: str,
    description: str,
    input_schema: type | dict[str, Any]
) -> Callable[[Callable[[Any], Awaitable[dict[str, Any]]]], SdkMcpTool[Any]]
```

**Parameters:**
- `name` (str): Unique identifier for the tool
- `description` (str): Human-readable description of what the tool does
- `input_schema` (type | dict[str, Any]): Schema defining the tool's input parameters

**Input Schema Options:**

1. Simple type mapping (recommended):
```python
{"text": str, "count": int, "enabled": bool}
```

2. JSON Schema format (for complex validation):
```python
{
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "count": {"type": "integer", "minimum": 0}
    },
    "required": ["text"]
}
```

**Example:**
```python
from claude_agent_sdk import tool

@tool("greet", "Greet a user", {"name": str})
async def greet(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [{
            "type": "text",
            "text": f"Hello, {args['name']}!"
        }]
    }
```

#### `create_sdk_mcp_server()`

Create an in-process MCP server that runs within your Python application.

```python
def create_sdk_mcp_server(
    name: str,
    version: str = "1.0.0",
    tools: list[SdkMcpTool[Any]] | None = None
) -> McpSdkServerConfig
```

**Parameters:**
- `name` (str): Unique identifier for the server
- `version` (str): Server version string (default: "1.0.0")
- `tools` (list[SdkMcpTool[Any]] | None): List of tool functions created with @tool decorator

**Example:**
```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("add", "Add two numbers", {"a": float, "b": float})
async def add(args):
    return {
        "content": [{
            "type": "text",
            "text": f"Sum: {args['a'] + args['b']}"
        }]
    }

@tool("multiply", "Multiply two numbers", {"a": float, "b": float})
async def multiply(args):
    return {
        "content": [{
            "type": "text",
            "text": f"Product: {args['a'] * args['b']}"
        }]
    }

calculator = create_sdk_mcp_server(
    name="calculator",
    version="2.0.0",
    tools=[add, multiply]
)

# Use with Claude
options = ClaudeAgentOptions(
    mcp_servers={"calc": calculator},
    allowed_tools=["mcp__calc__add", "mcp__calc__multiply"]
)
```

### Classes

#### `ClaudeSDKClient`

Maintains a conversation session across multiple exchanges. This is the Python equivalent of how the TypeScript SDK's `query()` function works internally.

```python
class ClaudeSDKClient:
    def __init__(self, options: ClaudeAgentOptions | None = None)
    async def connect(self, prompt: str | AsyncIterable[dict] | None = None) -> None
    async def query(self, prompt: str | AsyncIterable[dict], session_id: str = "default") -> None
    async def receive_messages(self) -> AsyncIterator[Message]
    async def receive_response(self) -> AsyncIterator[Message]
    async def interrupt(self) -> None
    async def disconnect(self) -> None
```

**Key Features:**
- **Session Continuity:** Maintains conversation context across multiple `query()` calls
- **Same Conversation:** Claude remembers previous messages in the session
- **Interrupt Support:** Can stop Claude mid-execution
- **Explicit Lifecycle:** You control when the session starts and ends
- **Response-driven Flow:** Can react to responses and send follow-ups
- **Custom Tools & Hooks:** Supports custom tools and hooks

**Methods:**

| Method | Description |
|--------|-------------|
| `__init__(options)` | Initialize the client with optional configuration |
| `connect(prompt)` | Connect to Claude with an optional initial prompt or message stream |
| `query(prompt, session_id)` | Send a new request in streaming mode |
| `receive_messages()` | Receive all messages from Claude as an async iterator |
| `receive_response()` | Receive messages until and including a ResultMessage |
| `interrupt()` | Send interrupt signal (only works in streaming mode) |
| `disconnect()` | Disconnect from Claude |

**Context Manager Support:**

The client can be used as an async context manager for automatic connection management:

```python
async with ClaudeSDKClient() as client:
    await client.query("Hello Claude")
    async for message in client.receive_response():
        print(message)
```

> **Important:** When iterating over messages, avoid using `break` to exit early as this can cause asyncio cleanup issues. Instead, let the iteration complete naturally or use flags to track when you've found what you need.

**Example - Continuing a Conversation:**

```python
import asyncio
from claude_agent_sdk import ClaudeSDKClient, AssistantMessage, TextBlock, ResultMessage

async def main():
    async with ClaudeSDKClient() as client:
        # First question
        await client.query("What's the capital of France?")
        
        # Process response
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")
        
        # Follow-up question - Claude remembers the previous context
        await client.query("What's the population of that city?")
        
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

asyncio.run(main())
```

### Types

#### `ClaudeAgentOptions`

Configuration dataclass for Claude Code queries.

```python
@dataclass
class ClaudeAgentOptions:
    allowed_tools: list[str] = field(default_factory=list)
    system_prompt: str | SystemPromptPreset | None = None
    mcp_servers: dict[str, McpServerConfig] | str | Path = field(default_factory=dict)
    permission_mode: PermissionMode | None = None
    continue_conversation: bool = False
    resume: str | None = None
    max_turns: int | None = None
    disallowed_tools: list[str] = field(default_factory=list)
    model: str | None = None
    permission_prompt_tool_name: str | None = None
    cwd: str | Path | None = None
    settings: str | None = None
    add_dirs: list[str | Path] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    extra_args: dict[str, str | None] = field(default_factory=dict)
    max_buffer_size: int | None = None
    stderr: Callable[[str], None] | None = None
    can_use_tool: CanUseTool | None = None
    hooks: dict[HookEvent, list[HookMatcher]] | None = None
    user: str | None = None
    include_partial_messages: bool = False
    fork_session: bool = False
    agents: dict[str, AgentDefinition] | None = None
    setting_sources: list[SettingSource] | None = None
```

**Key Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `allowed_tools` | list[str] | [] | List of allowed tool names |
| `system_prompt` | str \| SystemPromptPreset \| None | None | System prompt configuration |
| `mcp_servers` | dict \| str \| Path | {} | MCP server configurations or path to config file |
| `permission_mode` | PermissionMode \| None | None | Permission mode for tool usage |
| `cwd` | str \| Path \| None | None | Current working directory |
| `max_turns` | int \| None | None | Maximum conversation turns |
| `model` | str \| None | None | Claude model to use |
| `hooks` | dict[HookEvent, list[HookMatcher]] \| None | None | Hook configurations for intercepting events |
| `can_use_tool` | CanUseTool \| None | None | Tool permission callback function |
| `setting_sources` | list[SettingSource] \| None | None | Control which filesystem settings to load |

#### `SystemPromptPreset`

Configuration for using Claude Code's preset system prompt with optional additions.

```python
class SystemPromptPreset(TypedDict):
    type: Literal["preset"]
    preset: Literal["claude_code"]
    append: NotRequired[str]
```

**Example:**
```python
options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": "Additional instructions here"
    }
)
```

#### `PermissionMode`

Permission modes for controlling tool execution.

```python
PermissionMode = Literal[
    "default",           # Standard permission behavior
    "acceptEdits",       # Auto-accept file edits
    "plan",              # Planning mode - no execution
    "bypassPermissions"  # Bypass all permission checks (use with caution)
]
```

#### `SettingSource`

Controls which filesystem-based configuration sources the SDK loads settings from.

```python
SettingSource = Literal["user", "project", "local"]
```

| Value | Description | Path |
|-------|-------------|------|
| `"user"` | Global user settings | `~/.claude/settings.json` |
| `"project"` | Shared project settings (version controlled) | `.claude/settings.json` |
| `"local"` | Local project settings (gitignored) | `.claude/settings.local.json` |

**Default Behavior:** When `setting_sources` is omitted or `None`, the SDK does not load any filesystem settings.

**Example - Load project settings for CLAUDE.md:**
```python
options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code"
    },
    setting_sources=["project"],  # Required to load CLAUDE.md from project
    allowed_tools=["Read", "Write", "Edit"]
)
```

#### `AgentDefinition`

Configuration for a subagent defined programmatically.

```python
@dataclass
class AgentDefinition:
    description: str
    prompt: str
    tools: list[str] | None = None
    model: Literal["sonnet", "opus", "haiku", "inherit"] | None = None
```

#### Message Types

**`Message`** - Union type of all possible messages:
```python
Message = UserMessage | AssistantMessage | SystemMessage | ResultMessage
```

**`UserMessage`** - User input message:
```python
@dataclass
class UserMessage:
    content: str | list[ContentBlock]
```

**`AssistantMessage`** - Assistant response message:
```python
@dataclass
class AssistantMessage:
    content: list[ContentBlock]
    model: str
```

**`SystemMessage`** - System message with metadata:
```python
@dataclass
class SystemMessage:
    subtype: str
    data: dict[str, Any]
```

**`ResultMessage`** - Final result message with cost and usage information:
```python
@dataclass
class ResultMessage:
    subtype: str
    duration_ms: int
    duration_api_ms: int
    is_error: bool
    num_turns: int
    session_id: str
    total_cost_usd: float | None = None
    usage: dict[str, Any] | None = None
    result: str | None = None
```

#### Content Block Types

**`ContentBlock`** - Union type:
```python
ContentBlock = TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock
```

**`TextBlock`:**
```python
@dataclass
class TextBlock:
    text: str
```

**`ThinkingBlock`:**
```python
@dataclass
class ThinkingBlock:
    thinking: str
    signature: str
```

**`ToolUseBlock`:**
```python
@dataclass
class ToolUseBlock:
    id: str
    name: str
    input: dict[str, Any]
```

**`ToolResultBlock`:**
```python
@dataclass
class ToolResultBlock:
    tool_use_id: str
    content: str | list[dict[str, Any]] | None = None
    is_error: bool | None = None
```

### Error Types

**`ClaudeSDKError`** - Base exception class:
```python
class ClaudeSDKError(Exception):
    """Base error for Claude SDK."""
```

**`CLINotFoundError`** - Claude Code CLI not installed:
```python
class CLINotFoundError(CLIConnectionError):
    def __init__(self, message: str = "Claude Code not found", cli_path: str | None = None)
```

**`CLIConnectionError`** - Connection failure:
```python
class CLIConnectionError(ClaudeSDKError):
    """Failed to connect to Claude Code."""
```

**`ProcessError`** - Process failure:
```python
class ProcessError(ClaudeSDKError):
    def __init__(self, message: str, exit_code: int | None = None, stderr: str | None = None)
```

**`CLIJSONDecodeError`** - JSON parsing failure:
```python
class CLIJSONDecodeError(ClaudeSDKError):
    def __init__(self, line: str, original_error: Exception)
```

**Error Handling Example:**
```python
from claude_agent_sdk import (
    query,
    CLINotFoundError,
    ProcessError,
    CLIJSONDecodeError
)

try:
    async for message in query(prompt="Hello"):
        print(message)
except CLINotFoundError:
    print("Please install Claude Code: npm install -g @anthropic-ai/claude-code")
except ProcessError as e:
    print(f"Process failed with exit code: {e.exit_code}")
except CLIJSONDecodeError as e:
    print(f"Failed to parse response: {e}")
```

---

## Advanced Features

### Custom Tools (In-Process MCP Servers)

Custom tools are implemented as in-process MCP servers that run directly within your Python application, eliminating the need for separate processes.

**Benefits:**
- ✅ No subprocess management - runs in the same process
- ✅ Better performance - no IPC overhead for tool calls
- ✅ Simpler deployment - single Python process
- ✅ Easier debugging - all code runs in the same process
- ✅ Type safety - direct Python function calls with type hints

**Example:**
```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeSDKClient, ClaudeAgentOptions

# Define custom tools
@tool("calculate", "Perform mathematical calculations", {"expression": str})
async def calculate(args: dict[str, Any]) -> dict[str, Any]:
    try:
        result = eval(args["expression"], {"__builtins__": {}})
        return {
            "content": [{
                "type": "text",
                "text": f"Result: {result}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error: {str(e)}"
            }],
            "is_error": True
        }

@tool("get_time", "Get current time", {})
async def get_time(args: dict[str, Any]) -> dict[str, Any]:
    from datetime import datetime
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "content": [{
            "type": "text",
            "text": f"Current time: {current_time}"
        }]
    }

# Create SDK MCP server
my_server = create_sdk_mcp_server(
    name="utilities",
    version="1.0.0",
    tools=[calculate, get_time]
)

# Use with Claude
options = ClaudeAgentOptions(
    mcp_servers={"utils": my_server},
    allowed_tools=["mcp__utils__calculate", "mcp__utils__get_time"]
)

async with ClaudeSDKClient(options=options) as client:
    await client.query("What's 123 * 456?")
    async for message in client.receive_response():
        print(message)
```

**Mixed Server Support:**

You can use both SDK and external MCP servers together:

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "internal": sdk_server,      # In-process SDK server
        "external": {                # External subprocess server
            "type": "stdio",
            "command": "external-server"
        }
    }
)
```

### Hooks

Hooks are Python functions that Claude Code invokes at specific points in the agent loop. They enable deterministic processing and automated feedback.

**Supported Hook Events:**

```python
HookEvent = Literal[
    "PreToolUse",      # Called before tool execution
    "PostToolUse",     # Called after tool execution
    "UserPromptSubmit", # Called when user submits a prompt
    "Stop",            # Called when stopping execution
    "SubagentStop",    # Called when a subagent stops
    "PreCompact"       # Called before message compaction
]
```

**Hook Callback Type:**

```python
HookCallback = Callable[
    [dict[str, Any], str | None, HookContext],
    Awaitable[dict[str, Any]]
]
```

**Example - Blocking Dangerous Commands:**

```python
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, HookMatcher, HookContext

async def check_bash_command(input_data, tool_use_id, context):
    tool_name = input_data["tool_name"]
    tool_input = input_data["tool_input"]
    
    if tool_name != "Bash":
        return {}
    
    command = tool_input.get("command", "")
    block_patterns = ["rm -rf /", "format", "del /s"]
    
    for pattern in block_patterns:
        if pattern in command:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Dangerous pattern detected: {pattern}",
                }
            }
    return {}

options = ClaudeAgentOptions(
    allowed_tools=["Bash"],
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="Bash", hooks=[check_bash_command]),
        ],
    }
)

async with ClaudeSDKClient(options=options) as client:
    await client.query("Run: echo 'Hello'")  # Will work
    async for msg in client.receive_response():
        print(msg)
    
    await client.query("Run: rm -rf /")  # Will be blocked
    async for msg in client.receive_response():
        print(msg)
```

### Streaming Input

Both `query()` and `ClaudeSDKClient` support streaming input:

```python
async def message_stream():
    """Generate messages dynamically."""
    yield {"type": "text", "text": "Analyze the following data:"}
    await asyncio.sleep(0.5)
    yield {"type": "text", "text": "Temperature: 25°C"}
    await asyncio.sleep(0.5)
    yield {"type": "text", "text": "Humidity: 60%"}

async with ClaudeSDKClient() as client:
    await client.query(message_stream())
    async for message in client.receive_response():
        print(message)
```

### Interrupts

Use interrupts to stop Claude mid-execution (only with `ClaudeSDKClient`):

```python
async with ClaudeSDKClient(options=options) as client:
    # Start a long-running task
    await client.query("Count from 1 to 100 slowly")
    
    # Let it run for a bit
    await asyncio.sleep(2)
    
    # Interrupt the task
    await client.interrupt()
    print("Task interrupted!")
    
    # Send a new command
    await client.query("Just say hello instead")
    async for message in client.receive_response():
        pass
```

### Advanced Permission Control

```python
async def custom_permission_handler(
    tool_name: str,
    input_data: dict,
    context: dict
):
    """Custom logic for tool permissions."""
    
    # Block writes to system directories
    if tool_name == "Write" and input_data.get("file_path", "").startswith("/system/"):
        return {
            "behavior": "deny",
            "message": "System directory write not allowed",
            "interrupt": True
        }
    
    # Redirect sensitive file operations
    if tool_name in ["Write", "Edit"] and "config" in input_data.get("file_path", ""):
        safe_path = f"./sandbox/{input_data['file_path']}"
        return {
            "behavior": "allow",
            "updatedInput": {**input_data, "file_path": safe_path}
        }
    
    return {"behavior": "allow", "updatedInput": input_data}

options = ClaudeAgentOptions(
    can_use_tool=custom_permission_handler,
    allowed_tools=["Read", "Write", "Edit"]
)
```

---

## Examples

### Building a Continuous Conversation Interface

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock
import asyncio

class ConversationSession:
    """Maintains a single conversation session with Claude."""
    
    def __init__(self, options: ClaudeAgentOptions = None):
        self.client = ClaudeSDKClient(options)
        self.turn_count = 0
    
    async def start(self):
        await self.client.connect()
        print("Starting conversation session. Claude will remember context.")
        print("Commands: 'exit' to quit, 'interrupt' to stop, 'new' for new session")
        
        while True:
            user_input = input(f"\n[Turn {self.turn_count + 1}] You: ")
            
            if user_input.lower() == 'exit':
                break
            elif user_input.lower() == 'interrupt':
                await self.client.interrupt()
                print("Task interrupted!")
                continue
            elif user_input.lower() == 'new':
                await self.client.disconnect()
                await self.client.connect()
                self.turn_count = 0
                print("Started new conversation session")
                continue
            
            await client.query(user_input)
            self.turn_count += 1
            
            print(f"[Turn {self.turn_count}] Claude: ", end="")
            async for message in self.client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(block.text, end="")
            print()
        
        await self.client.disconnect()
        print(f"Conversation ended after {self.turn_count} turns.")

async def main():
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Bash"],
        permission_mode="acceptEdits"
    )
    session = ConversationSession(options)
    await session.start()

asyncio.run(main())
```

### Real-time Progress Monitoring

```python
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    ToolUseBlock,
    ToolResultBlock,
    TextBlock
)

async def monitor_progress():
    options = ClaudeAgentOptions(
        allowed_tools=["Write", "Bash"],
        permission_mode="acceptEdits"
    )
    
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Create 5 Python files with sorting algorithms")
        
        async for message in client.receive_messages():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ToolUseBlock):
                        if block.name == "Write":
                            file_path = block.input.get("file_path", "")
                            print(f"🔨 Creating: {file_path}")
                    elif isinstance(block, ToolResultBlock):
                        print(f"✅ Completed tool execution")
                    elif isinstance(block, TextBlock):
                        print(f"💭 Claude: {block.text[:100]}...")
            
            if hasattr(message, 'subtype') and message.subtype in ['success', 'error']:
                print(f"\n🎯 Task completed!")
                break

asyncio.run(monitor_progress())
```

---

## Migration Guide

### Migrating from Claude Code SDK (< 0.1.0)

If you're upgrading from the Claude Code SDK (versions < 0.1.0), note these breaking changes:

**1. Package Rename:**
```python
# Before
from claude_code_sdk import query, ClaudeCodeOptions

# After
from claude_agent_sdk import query, ClaudeAgentOptions
```

**2. Options Rename:**
```python
# Before
options = ClaudeCodeOptions(...)

# After
options = ClaudeAgentOptions(...)
```

**3. Settings Isolation:**

The SDK now defaults to **not loading** filesystem settings. To load settings:

```python
# Load all settings (legacy behavior)
options = ClaudeAgentOptions(
    setting_sources=["user", "project", "local"]
)

# Load only project settings
options = ClaudeAgentOptions(
    setting_sources=["project"]
)
```

**4. System Prompt Configuration:**

System prompts are now merged:

```python
# Use Claude Code's preset system prompt
options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code"
    }
)

# Extend the preset with additional instructions
options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": "Additional instructions here"
    }
)
```

### Migrating from External MCP Servers to SDK Servers

```python
# BEFORE: External MCP server (separate process)
options = ClaudeAgentOptions(
    mcp_servers={
        "calculator": {
            "type": "stdio",
            "command": "python",
            "args": ["-m", "calculator_server"]
        }
    }
)

# AFTER: SDK MCP server (in-process)
from my_tools import add, subtract

calculator = create_sdk_mcp_server(
    name="calculator",
    tools=[add, subtract]
)

options = ClaudeAgentOptions(
    mcp_servers={"calculator": calculator}
)
```

---

## Available Tools

Claude Code provides several built-in tools:

- **`Bash`** - Execute shell commands
- **`Read`** - Read file contents
- **`Write`** - Write files
- **`Edit`** - Edit files with string replacement
- **`Glob`** - Find files matching patterns
- **`Grep`** - Search file contents
- **`Task`** - Delegate to subagents
- **`NotebookEdit`** - Edit Jupyter notebooks
- **`WebFetch`** - Fetch web content
- **`WebSearch`** - Search the web
- **`TodoWrite`** - Manage todo lists
- **`BashOutput`** - Check background shell output
- **`KillBash`** - Kill background shells
- **`ExitPlanMode`** - Exit planning mode
- **`ListMcpResources`** - List MCP resources
- **`ReadMcpResource`** - Read MCP resources

For detailed tool schemas and parameters, see the [official documentation](https://docs.claude.com/en/docs/claude-code/settings#tools-available-to-claude).

---

## Additional Resources

- **GitHub Repository:** [anthropics/claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python)
- **API Documentation:** [docs.claude.com/en/api/agent-sdk/python](https://docs.claude.com/en/api/agent-sdk/python)
- **Examples Directory:** [GitHub Examples](https://github.com/anthropics/claude-agent-sdk-python/tree/main/examples)
- **Claude Code Documentation:** [docs.claude.com/en/docs/claude-code](https://docs.claude.com/en/docs/claude-code)
- **MCP Documentation:** [Model Context Protocol](https://modelcontextprotocol.io/)

---

## License

MIT License - See [LICENSE](https://github.com/anthropics/claude-agent-sdk-python/blob/main/LICENSE) for details.

---

*Last Updated: October 16, 2025*
*SDK Version: 0.1.3*
