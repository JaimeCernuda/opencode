# OpenCode TUI Architecture Documentation

## Overview

The OpenCode TUI (Terminal User Interface) is a Go-based terminal application built with the Bubbletea framework. It provides an interactive interface for AI-assisted coding sessions, managing conversations with AI agents, and executing commands.

## Project Structure

```
packages/tui/
├── cmd/opencode/          # Application entry point
│   └── main.go           # Main application initialization
├── input/                # Custom input handling (forked from charmbracelet/x/input)
│   ├── driver.go         # Terminal input driver
│   ├── key.go            # Keyboard input handling
│   ├── mouse.go          # Mouse input handling
│   ├── paste.go          # Paste detection
│   └── ...               # Other input utilities
├── internal/
│   ├── api/              # REST API client communication
│   ├── app/              # Core application logic and state
│   ├── attachment/       # File attachment handling
│   ├── clipboard/        # Clipboard operations
│   ├── commands/         # Command registry and execution
│   ├── completions/      # Auto-completion providers
│   ├── components/       # UI components
│   │   ├── chat/         # Chat interface (editor, messages)
│   │   ├── commands/     # Command palette
│   │   ├── dialog/       # Modal dialogs
│   │   ├── diff/         # Diff viewer
│   │   ├── list/         # List components
│   │   ├── modal/        # Modal windows
│   │   ├── qr/           # QR code display
│   │   ├── status/       # Status bar
│   │   ├── textarea/     # Text input area
│   │   └── toast/        # Toast notifications
│   ├── id/               # ID generation utilities
│   ├── layout/           # Layout management
│   ├── styles/           # UI styling and theming
│   ├── theme/            # Theme definitions and loader
│   ├── tui/              # Main TUI model and update logic
│   ├── util/             # Utility functions
│   └── viewport/         # Scrollable viewport component
├── go.mod                # Go module definition
└── go.sum                # Go module checksums
```

## Core Components

### 1. Main Application (`cmd/opencode/main.go`)

**Purpose**: Application entry point, initialization, and lifecycle management.

**Key Responsibilities**:
- Parse command-line flags (`--model`, `--prompt`, `--agent`, `--session`)
- Initialize HTTP client for API communication
- Load project configuration, agents, and paths
- Set up logging with API log handler
- Initialize clipboard support
- Create and run the Bubbletea program
- Handle graceful shutdown (SIGTERM, SIGINT)
- Start SSE (Server-Sent Events) stream for real-time updates
- Start API control channel for external commands

**Dependencies**:
- `github.com/charmbracelet/bubbletea/v2` - TUI framework
- `github.com/sst/opencode-sdk-go` - OpenCode SDK client
- `github.com/spf13/pflag` - CLI flag parsing

### 2. Application Core (`internal/app/app.go`)

**Purpose**: Core application state and business logic.

**Key Structures**:

```go
type App struct {
    Project           opencode.Project
    Agents            []opencode.Agent
    Providers         []opencode.Provider
    Version           string
    StatePath         string
    Config            *opencode.Config
    Client            *opencode.Client
    State             *State
    AgentIndex        int
    Provider          *opencode.Provider
    Model             *opencode.Model
    Session           *opencode.Session
    Messages          []Message
    Permissions       []opencode.Permission
    CurrentPermission opencode.Permission
    Commands          commands.CommandRegistry
    InitialModel      *string
    InitialPrompt     *string
    InitialAgent      *string
    InitialSession    *string
    compactCancel     context.CancelFunc
    IsLeaderSequence  bool
    IsBashMode        bool
    ScrollSpeed       int
}

type Message struct {
    Info  opencode.MessageUnion
    Parts []opencode.PartUnion
}
```

**Key Methods**:

- `New()` - Initialize application with configuration
- `Agent()` - Get current agent
- `SwitchAgent()` / `SwitchAgentReverse()` - Cycle through agents
- `CycleRecentModel()` - Cycle through recently used models
- `InitializeProvider()` - Load and select AI provider/model
- `InitializeProject()` - Create initial session
- `CompactSession()` - Summarize session context
- `CreateSession()` - Create new chat session
- `SendPrompt()` - Send user message
- `SendCommand()` - Execute custom command
- `SendShell()` - Execute shell command
- `Cancel()` - Abort running operation
- `ListSessions()` / `DeleteSession()` / `UpdateSession()` - Session management
- `ListMessages()` - Retrieve session messages
- `ListProviders()` - Get available AI providers
- `IsBusy()` - Check if AI is processing
- `SaveState()` - Persist application state

**Key Messages** (Bubbletea):
- `SessionCreatedMsg` - New session created
- `SessionSelectedMsg` - Session selected/loaded
- `MessageRevertedMsg` - Message reverted (undo)
- `SessionUnrevertedMsg` - Message unreverted (redo)
- `SessionLoadedMsg` - Session loaded successfully
- `ModelSelectedMsg` - AI model selected
- `AgentSelectedMsg` - Agent switched
- `SessionClearedMsg` - Session cleared
- `CompactSessionMsg` - Session compacted
- `SendPrompt` - Send user prompt
- `SendShell` - Send shell command
- `SendCommand` - Send custom command
- `SetEditorContentMsg` - Update editor content
- `FileRenderedMsg` - File rendered
- `PermissionRespondedToMsg` - Permission request handled

### 3. Application State (`internal/app/state.go`)

**Purpose**: Persistent application state (saved as TOML).

**Structure**:

```go
type State struct {
    Theme              string
    AgentModel         map[string]AgentModel  // Agent → Model mapping
    Provider           string                 // Legacy: provider ID
    Model              string                 // Legacy: model ID
    Agent              string                 // Current agent name
    RecentlyUsedModels []ModelUsage          // Model usage history
    RecentlyUsedAgents []AgentUsage          // Agent usage history
    MessageHistory     []Prompt              // Prompt history
    ShowToolDetails    *bool                 // UI preference
    ShowThinkingBlocks *bool                 // UI preference
}

type ModelUsage struct {
    ProviderID string
    ModelID    string
    LastUsed   time.Time
}

type AgentUsage struct {
    AgentName string
    LastUsed  time.Time
}

type AgentModel struct {
    ProviderID string
    ModelID    string
}
```

**Key Methods**:
- `UpdateModelUsage()` - Track model usage
- `RemoveModelFromRecentlyUsed()` - Clean up model history
- `UpdateAgentUsage()` - Track agent usage
- `RemoveAgentFromRecentlyUsed()` - Clean up agent history
- `AddPromptToHistory()` - Save prompt to history
- `SaveState()` - Write state to TOML file
- `LoadState()` - Load state from TOML file

**State File Location**: `<state_path>/tui` (TOML format)

### 4. TUI Model (`internal/tui/tui.go`)

**Purpose**: Main Bubbletea model handling UI updates and user input.

**Structure**:

```go
type Model struct {
    width, height        int
    app                  *app.App
    modal                layout.Modal
    status               status.StatusComponent
    editor               chat.EditorComponent
    messages             chat.MessagesComponent
    completions          dialog.CompletionDialog
    commandProvider      completions.CompletionProvider
    fileProvider         completions.CompletionProvider
    symbolsProvider      completions.CompletionProvider
    agentsProvider       completions.CompletionProvider
    showCompletionDialog bool
    leaderBinding        *key.Binding
    toastManager         *toast.ToastManager
    interruptKeyState    InterruptKeyState
    exitKeyState         ExitKeyState
    messagesRight        bool
}
```

**Key Methods**:
- `Init()` - Initialize TUI components
- `Update()` - Handle all messages (keyboard, API events, etc.)
- `View()` - Render the UI
- `Cleanup()` - Clean up resources on exit

**Input Handling**:
1. Permission requests (enter/esc/a)
2. Bash mode (special prompt mode)
3. Active modals (priority handling)
4. Leader key sequences (multi-key commands)
5. Completion dialog trigger (`/`)
6. Command execution
7. Standard key bindings

### 5. API Communication (`internal/api/api.go`)

**Purpose**: Handle REST API communication with OpenCode server.

**Structure**:

```go
type Request struct {
    Path string
    Body json.RawMessage
}
```

**Key Functions**:
- `Start()` - Poll for TUI control commands (blocking loop)
- `Reply()` - Send response back to API

**Flow**:
1. Poll `/tui/control/next` for incoming requests
2. Send request as Bubbletea message
3. TUI processes request
4. Reply via `/tui/control/response`

### 6. Components

#### Chat Components (`internal/components/chat/`)
- **EditorComponent**: Multi-line text editor with attachments
- **MessagesComponent**: Scrollable message history with rendering

#### Dialog Components (`internal/components/dialog/`)
- **CompletionDialog**: Auto-completion for commands, files, symbols

#### Status Component (`internal/components/status/`)
- **StatusComponent**: Bottom status bar with model/agent info

#### Toast Component (`internal/components/toast/`)
- **ToastManager**: Non-blocking notifications

#### Modal Components (`internal/components/modal/`)
- Various modal dialogs (sessions, models, permissions, etc.)

### 7. Theme System (`internal/theme/`)

**Purpose**: Customizable color themes.

**Key Features**:
- JSON-based theme definitions
- Color reference resolution (`$colors.primary`)
- System theme detection
- Built-in themes (opencode, vs-code-dark, etc.)
- Custom theme loading from directories

**Theme Interface**:

```go
type Theme interface {
    // Core colors
    Primary() AdaptiveColor
    Secondary() AdaptiveColor
    Accent() AdaptiveColor
    
    // Status colors
    Error() AdaptiveColor
    Warning() AdaptiveColor
    Success() AdaptiveColor
    Info() AdaptiveColor
    
    // Text colors
    Text() AdaptiveColor
    TextMuted() AdaptiveColor
    
    // Background colors
    Background() AdaptiveColor
    BackgroundPanel() AdaptiveColor
    BackgroundElement() AdaptiveColor
    
    // Border colors
    Border() AdaptiveColor
    BorderActive() AdaptiveColor
    BorderSubtle() AdaptiveColor
    
    // Diff colors
    DiffAdded() AdaptiveColor
    DiffRemoved() AdaptiveColor
    // ... more diff colors
    
    // Markdown colors
    MarkdownText() AdaptiveColor
    MarkdownHeading() AdaptiveColor
    // ... more markdown colors
    
    // Syntax colors
    SyntaxComment() AdaptiveColor
    SyntaxKeyword() AdaptiveColor
    // ... more syntax colors
}
```

### 8. Commands (`internal/commands/`)

**Purpose**: Command registry and keybinding management.

**Key Features**:
- Built-in commands (copy, paste, submit, etc.)
- Custom commands from config
- Leader key support
- Multi-key sequences
- Command matching and execution

## Data Flow

### 1. Session Initialization

```
main.go
  ↓ Create HTTP client
  ↓ Load project, agents, paths
  ↓
app.New()
  ↓ Load config, state
  ↓ Set theme
  ↓ Create App instance
  ↓
tui.NewModel()
  ↓ Initialize components
  ↓
program.Run()
  ↓ Start event loop
  ↓
app.InitializeProvider()
  ↓ Load providers
  ↓ Select model (priority order)
  ↓ Load initial session (if --session flag)
```

### 2. Model Selection Priority

1. Command line `--model` flag
2. Config file `model` setting
3. Current agent's preferred model
4. Most recently used model
5. State-based model (legacy)
6. Internal priority (Anthropic preferred)
7. First available provider

### 3. Message Sending Flow

```
User Input
  ↓
editor.Submit()
  ↓
SendPrompt message
  ↓
app.SendPrompt()
  ↓ Create session if needed
  ↓ Generate message ID
  ↓ Add to messages list
  ↓
client.Session.Prompt()
  ↓ POST to API
  ↓
SSE Stream
  ↓ Real-time events
  ↓
program.Send(event)
  ↓
tui.Update()
  ↓ Update messages
  ↓
tui.View()
  ↓ Re-render UI
```

### 4. Event Streaming Flow

```
main.go
  ↓
httpClient.Event.ListStreaming()
  ↓ Open SSE connection
  ↓ Receive events:
    - message.new
    - message.completed
    - session.updated
    - tool.started
    - tool.completed
    - etc.
  ↓
program.Send(event)
  ↓
tui.Update()
  ↓ Handle specific event type
  ↓ Update app state
  ↓ Update UI components
```

## API Endpoints Used

The TUI communicates with the OpenCode server via REST API:

### Project & Configuration
- `GET /project/current` - Get current project info
- `GET /agent/list` - List available agents
- `GET /path` - Get path configuration
- `GET /config` - Get user configuration
- `GET /app/providers` - List AI providers and models
- `GET /command/list` - Get custom commands

### Session Management
- `POST /session` - Create new session
- `GET /session` - List sessions
- `GET /session/{id}` - Get session details
- `DELETE /session/{id}` - Delete session
- `PATCH /session/{id}` - Update session (title)
- `POST /session/{id}/init` - Initialize session
- `POST /session/{id}/prompt` - Send prompt
- `POST /session/{id}/command` - Execute command
- `POST /session/{id}/shell` - Execute shell command
- `POST /session/{id}/abort` - Cancel operation
- `POST /session/{id}/summarize` - Compact session
- `GET /session/{id}/messages` - Get session messages

### Permissions
- `POST /session/{id}/permissions/{permissionId}/respond` - Respond to permission request

### Events
- `GET /event` (SSE) - Real-time event stream

### TUI Control
- `GET /tui/control/next` - Poll for control commands
- `POST /tui/control/response` - Send response

### Logging
- `POST /log` - Send log entries

## Key Features

### 1. Multi-Agent Support
- Switch between different AI agents (build, ship, inspect)
- Each agent has its own persona and capabilities
- Agent-specific model preferences

### 2. Model Management
- Support for multiple AI providers (Anthropic, OpenAI, etc.)
- Model switching during session
- Recent model history with quick cycling
- Per-agent model preferences

### 3. Session Management
- Create, list, delete sessions
- Load previous sessions
- Session compaction (summarization)
- Persistent session history

### 4. Rich Text Editing
- Multi-line input with syntax highlighting
- File attachments
- Command history
- Bash mode for shell commands
- Auto-completion for commands, files, symbols

### 5. Real-Time Updates
- SSE-based event streaming
- Live message updates
- Tool execution status
- Permission requests

### 6. Theming
- Built-in themes
- Custom theme support
- System theme integration
- Dark/light mode support

### 7. Keyboard Shortcuts
- Configurable keybindings
- Leader key sequences
- Modal-aware input handling
- Vim-style navigation

### 8. Clipboard Integration
- Copy messages
- Copy code blocks
- OSC52 support for remote terminals
- Native clipboard fallback

## Configuration

### Config File Format (TOML)

The application reads configuration from the OpenCode config file:

```toml
model = "anthropic/claude-3-5-sonnet-20241022"
theme = "opencode"

[keybinds]
leader = "ctrl+x"

[tui]
scroll_speed = 3

[[command]]
name = "custom-command"
description = "My custom command"
command = "echo Hello"
args = ["arg1", "arg2"]
```

### State File Format (TOML)

The TUI state is persisted at `<state_path>/tui`:

```toml
theme = "opencode"
agent = "build"
provider = "anthropic"  # legacy
model = "claude-3-5-sonnet-20241022"  # legacy

[agent_model.build]
provider_id = "anthropic"
model_id = "claude-3-5-sonnet-20241022"

[[recently_used_models]]
provider_id = "anthropic"
model_id = "claude-3-5-sonnet-20241022"
last_used = 2024-10-17T10:30:00Z

[[recently_used_agents]]
agent_name = "build"
last_used = 2024-10-17T10:30:00Z

[[message_history]]
text = "Previous prompt"
```

## Dependencies

### Core
- **Bubbletea** (`github.com/charmbracelet/bubbletea/v2`) - TUI framework
- **Lipgloss** (`github.com/charmbracelet/lipgloss/v2`) - Styling and layout
- **Bubbles** (`github.com/charmbracelet/bubbles/v2`) - Reusable components
- **OpenCode SDK** (`github.com/sst/opencode-sdk-go`) - API client

### Utilities
- **pflag** (`github.com/spf13/pflag`) - CLI flags
- **uuid** (`github.com/google/uuid`) - UUID generation
- **fsnotify** (`github.com/fsnotify/fsnotify`) - File watching
- **glamour** (`github.com/charmbracelet/glamour`) - Markdown rendering
- **chroma** (`github.com/alecthomas/chroma/v2`) - Syntax highlighting
- **toml** (`github.com/BurntSushi/toml`) - TOML parsing
- **qr** (`rsc.io/qr`) - QR code generation

### Replace Directives
- `github.com/charmbracelet/x/input` → `./input` (custom fork)
- `github.com/sst/opencode-sdk-go` → `../sdk/go` (local SDK)

## Building and Running

### Build
```bash
cd packages/tui
go build -o opencode ./cmd/opencode
```

### Run
```bash
# Basic usage
./opencode

# With options
./opencode --model anthropic/claude-3-5-sonnet --prompt "Hello" --agent build --session <id>

# With custom server
OPENCODE_SERVER=http://localhost:8080 ./opencode

# With custom theme
OPENCODE_THEME=vs-code-dark ./opencode
```

## Testing

The codebase includes unit tests for various components:
- Theme loading and resolution
- Key event parsing
- Input driver functionality
- Viewport scrolling

Run tests:
```bash
go test ./...
```

## Error Handling

The application uses structured logging (`log/slog`) with the following levels:
- **Debug**: Detailed diagnostic information
- **Info**: General informational messages
- **Warn**: Warning messages
- **Error**: Error messages

Logs are sent to the OpenCode server via the `/log` endpoint.

## Graceful Shutdown

The application handles SIGTERM and SIGINT signals:
1. Capture signal
2. Call `tuiModel.Cleanup()`
3. Call `program.Quit()`
4. Exit cleanly

## Special Modes

### 1. Bash Mode
- Triggered by special input
- Allows direct shell command execution
- Indicated by special prompt
- Exit with Enter (submit), Esc, or Ctrl+C

### 2. Leader Mode
- Multi-key command sequences
- Triggered by leader key (default: Ctrl+X)
- Displays available commands
- Timeout after 1 second

### 3. Permission Mode
- Blocks input during permission requests
- Shows permission details
- Options: Enter (once), A (always), Esc (reject)
- Queues multiple requests

## Performance Considerations

1. **Viewport Memoization**: Caches rendered content to avoid re-rendering
2. **Lazy Loading**: Messages loaded on demand
3. **Debounced Input**: Interrupt and exit keys use debouncing
4. **Background Color Detection**: Disabled on WSL due to compatibility issues
5. **Event Streaming**: Efficient SSE-based updates instead of polling

## Future Enhancements

Potential areas for improvement:
1. Enhanced error recovery
2. Offline mode support
3. Plugin system
4. More themes and customization
5. Advanced search and filtering
6. Collaborative features
7. Performance profiling tools
8. Better accessibility support

---

**Version**: Based on OpenCode TUI as of October 2024  
**Go Version**: 1.24.0  
**Framework**: Bubbletea v2.0.0-beta.4
