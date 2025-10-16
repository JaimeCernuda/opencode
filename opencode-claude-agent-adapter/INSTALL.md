# Installation Guide

## Prerequisites

1. **Python 3.11+**
   ```bash
   python --version  # Should show 3.11 or higher
   ```

2. **UV Package Manager (recommended)** or pip
   ```bash
   # Install uv if you don't have it
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Anthropic API Key**
   - Get your API key from: https://console.anthropic.com/
   - You'll need this for the Claude Agent SDK

## Step-by-Step Installation

### 1. Navigate to the project directory

```bash
cd opencode-claude-agent-adapter
```

### 2. Set your API key

The Claude Agent SDK automatically reads from the `ANTHROPIC_API_KEY` environment variable.

**Option A: Export directly (temporary)**
```bash
export ANTHROPIC_API_KEY=sk-ant-your-actual-api-key-here
```

**Option B: Create .env file (persistent)**
```bash
# Create .env file
echo "ANTHROPIC_API_KEY=sk-ant-your-actual-api-key-here" > .env

# Optional: Add more configuration
echo "CLAUDE_MODEL=claude-opus-4-20250514" >> .env
echo "OPENCODE_PORT=3000" >> .env
echo "OPENCODE_HOST=127.0.0.1" >> .env
```

The server will load `.env` automatically if it exists.

### 3. Install dependencies

**Option A: Using UV (recommended)**

```bash
# Install in development mode
uv pip install -e .
```

**Option B: Using pip**

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install
pip install -e .
```

### 4. Verify Installation

```bash
# Verify API key is set
echo $ANTHROPIC_API_KEY

# Should output: sk-ant-...
# If empty, set it: export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## Running the Server

### Option 1: Using the run script (easiest)

```bash
chmod +x run.sh
./run.sh
```

### Option 2: Direct Python

```bash
# Make sure ANTHROPIC_API_KEY is set
python src/opencode_claude_agent/server.py
```

### Option 3: Using uv run

```bash
uv run python src/opencode_claude_agent/server.py
```

### Option 4: Using installed command

```bash
# If installed with pip in a venv
opencode-claude-agent
```

You should see:

```
================================================================================
OpenCode Claude Agent Adapter Starting...
================================================================================

Server: http://127.0.0.1:3000
Model: claude-opus-4-20250514

To connect OpenCode TUI:
  OPENCODE_SERVER=http://127.0.0.1:3000 <path-to-tui-binary>

================================================================================

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:3000 (Press CTRL+C to quit)
```

## Connecting OpenCode TUI

### 1. Build OpenCode TUI (if not already built)

```bash
# From the opencode root directory
cd packages/tui/cmd/opencode
go build -o tui main.go
```

### 2. Run OpenCode TUI pointing to your adapter

**Linux/Mac:**

```bash
export OPENCODE_SERVER=http://localhost:3000
./tui
```

**Windows PowerShell:**

```powershell
$env:OPENCODE_SERVER="http://localhost:3000"
.\tui.exe
```

**Windows CMD:**

```cmd
set OPENCODE_SERVER=http://localhost:3000
tui.exe
```

### 3. Test the connection

1. The TUI should start and connect to your server
2. You should see connection logs in the server terminal
3. Try sending a message like "Hello, Claude!"
4. You should see a streaming response from Claude

## Troubleshooting

### "ANTHROPIC_API_KEY environment variable is required"

The Claude Agent SDK needs this environment variable. Make sure it's set:

```bash
# Check if set
echo $ANTHROPIC_API_KEY

# If empty, set it
export ANTHROPIC_API_KEY=sk-ant-your-key-here

# OR create .env file
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > .env
```

The API key should start with `sk-ant-`

### "Port 3000 already in use"

Change the port in `.env`:
```bash
OPENCODE_PORT=3001
```

And update the TUI connection:
```bash
export OPENCODE_SERVER=http://localhost:3001
```

### Claude Agent SDK import errors

Make sure the SDK is installed:
```bash
uv pip install git+https://github.com/anthropics/claude-agent-sdk-python.git
```

### TUI can't connect

1. Verify the server is running
2. Check the `OPENCODE_SERVER` environment variable is set correctly
3. Make sure no firewall is blocking port 3000
4. Check server logs for error messages

## Uninstallation

```bash
# If using pip with venv
deactivate
rm -rf venv

# Remove the project
cd ..
rm -rf opencode-claude-agent-adapter
```

## Next Steps

- Read [USAGE.md](USAGE.md) for detailed usage instructions
- Check [README.md](README.md) for architecture overview
- See the prompt.md file for implementation details
