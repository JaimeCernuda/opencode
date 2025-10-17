# Helios Quick Start Guide

Complete manual deployment guide for Helios with your custom adapter server.

## What is This Setup?

Helios consists of two components:
1. **Your Adapter Server** - Python server at `opencode-tui-adapter/` (implements OpenCode API protocol)
2. **Helios TUI** - The rebranded terminal interface

## Prerequisites

- Python 3.10+ with `uv` installed
- Go 1.24.x (for TUI)
- Python 3.8+ (for rebranding script)

---

## Part 1: Deploy Your Adapter Server

### Step 1: Navigate to Adapter Directory

```bash
cd /home/jcernuda/opencode-1/opencode-tui-adapter
```

### Step 2: Start the Server

```bash
uv run python src/opencode_tui_adapter/server.py
```

Expected output:
```
================================================================================
🚀 OpenCode TUI Logging Server Starting...
================================================================================
Server running at http://localhost:3000
```

**Keep this terminal running!** The adapter server must stay active.

The server will:
- Run on `http://localhost:3000`
- Log all incoming requests
- Return dummy/test responses for protocol testing

### Step 3: Verify Server is Running

Open a new terminal and test:

```bash
curl http://localhost:3000/project/current
```

You should see JSON output.

---

## Part 2: Deploy the Helios TUI

### Step 1: Apply Helios Rebranding

In a new terminal:

```bash
cd /home/jcernuda/opencode-1
python3 rebrand-helios.py
```

Expected output:
```
============================================================
🌞 HELIOS REBRANDING SCRIPT - APPLYING CHANGES
============================================================
...
✨ Rebranding complete! 4 files modified.
```

### Step 2: Build the Helios TUI

```bash
cd /home/jcernuda/opencode-1/packages/tui
go build -o helios ./cmd/opencode
```

This creates the `helios` binary (~27MB).

### Step 3: Configure Server Connection

```bash
export HELIOS_SERVER=http://localhost:3000
```

**Note:** Port 3000 (not 41800) - this connects to YOUR adapter, not the OpenCode server.

### Step 4: Run Helios

```bash
./helios
```

You should see:
- Helios TUI with sun logo and warm colors
- In the adapter terminal: detailed request logs showing every TUI interaction

---

## Quick Reference Commands

### Start Everything (Two Terminals)

**Terminal 1 - Adapter Server:**
```bash
cd /home/jcernuda/opencode-1/opencode-tui-adapter
uv run python src/opencode_tui_adapter/server.py
```

**Terminal 2 - Helios TUI:**
```bash
cd /home/jcernuda/opencode-1
python3 rebrand-helios.py
cd packages/tui
go build -o helios ./cmd/opencode
export HELIOS_SERVER=http://localhost:3000
./helios
```

### One-Liner After Initial Setup

If you've already built everything once:

**Terminal 1:**
```bash
cd /home/jcernuda/opencode-1/opencode-tui-adapter && uv run python src/opencode_tui_adapter/server.py
```

**Terminal 2:**
```bash
HELIOS_SERVER=http://localhost:3000 /home/jcernuda/opencode-1/packages/tui/helios
```

---

## Using the IO Warp Script (Easy Mode)

The adapter includes an `iowarp.py` script that handles everything:

```bash
cd /home/jcernuda/opencode-1/opencode-tui-adapter
uv run python iowarp.py
```

This will:
1. ✅ Build the TUI if needed
2. ✅ Start the adapter server
3. ✅ Launch the TUI connected to the server
4. ✅ Clean up when you exit (Ctrl+C)

**BUT** this uses the vanilla OpenCode TUI, not Helios. For Helios branding, use the manual steps above.

---

## What You'll See

### In the Adapter Server Terminal:

Every TUI interaction is logged in detail:

```
================================================================================
[14:23:45.123] POST /session/sess_123456/message
================================================================================
{
  "body": {
    "messageID": "msg_789",
    "agent": "test-agent",
    "parts": [
      {
        "type": "text",
        "text": "Hello Helios!"
      }
    ]
  }
}

🚀 🚀 🚀 MESSAGE RECEIVED for session: sess_123456 🚀 🚀 🚀

📋 Message Details:
   Message ID: msg_789
   Agent: test-agent
   Model: test/test-model

📦 Parts (1):
   Part 1:
      Type: text
      Text: Hello Helios!
```

### In the Helios TUI:

- Helios logo (stylized HELIOS text)
- Sun loading screen (☀️ ASCII art)
- Warm orange/gold theme
- Normal TUI functionality (type messages, use slash commands, etc.)

---

## Updating from Upstream OpenCode

To get latest OpenCode TUI features while keeping Helios branding:

### Step 1: Sync with Upstream

```bash
cd /home/jcernuda/opencode-1
git fetch upstream
git merge upstream/dev
```

### Step 2: Revert Old Branding

```bash
python3 rebrand-helios.py --revert
```

### Step 3: Apply Fresh Branding

```bash
python3 rebrand-helios.py
```

### Step 4: Rebuild TUI

```bash
cd packages/tui
go build -o helios ./cmd/opencode
```

Done! Latest TUI features with Helios branding.

---

## Troubleshooting

### Adapter server won't start

**Problem:** Port 3000 already in use

```bash
# Check what's using the port
lsof -i :3000

# Kill the process or modify server.py to use different port
```

**Problem:** uv not installed

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

**Problem:** Python dependencies missing

```bash
cd /home/jcernuda/opencode-1/opencode-tui-adapter
uv sync
```

### TUI can't connect

**Problem:** Server not running

```bash
# Check if adapter is accessible
curl http://localhost:3000/project/current
```

**Problem:** Wrong server URL

```bash
# Make sure HELIOS_SERVER points to adapter (port 3000)
echo $HELIOS_SERVER
# Should be: http://localhost:3000

# Set it correctly
export HELIOS_SERVER=http://localhost:3000
```

**Problem:** Using wrong port

The adapter runs on port **3000**, not 41800 (which is the full OpenCode server).

### Build fails

**Problem:** Old branding conflicts

```bash
# Clean everything
python3 rebrand-helios.py --revert
cd packages/tui
go clean
go build -o helios ./cmd/opencode
```

**Problem:** Go modules out of sync

```bash
cd packages/tui
go mod tidy
go build -o helios ./cmd/opencode
```

### Revert to vanilla OpenCode TUI

```bash
python3 rebrand-helios.py --revert
cd packages/tui
go build -o opencode ./cmd/opencode
export OPENCODE_SERVER=http://localhost:3000
./opencode
```

---

## Environment Variables

### Adapter Server

No special environment variables needed. The adapter runs on `http://localhost:3000` by default.

### Helios TUI

| Variable | Description | Value |
|----------|-------------|-------|
| `HELIOS_SERVER` | Your adapter server URL | `http://localhost:3000` |
| `HELIOS_THEME` | Force specific theme | `helios`, `nord`, `gruvbox` |

---

## What Gets Rebranded?

The rebranding script modifies the TUI only:

1. **Logo** - "open/code" → stylized "HELIOS"
2. **Loading Screen** - Empty → Sun ASCII art ☀️
3. **Status Bar** - "opencode VERSION" → "helios VERSION"
4. **Environment Variables** - `OPENCODE_SERVER` → `HELIOS_SERVER`
5. **Config Paths** - `.opencode/` → `.helios/`
6. **Theme** - Custom sun-inspired color scheme (warm oranges/golds)

Your adapter server is NOT modified - only the TUI client is rebranded.

---

## Next Steps for Your Adapter

According to the adapter README, you can:

1. **Understand the Protocol** - Watch the logs to see how TUI communicates
2. **Replace Dummy Responses** - Add real CrewAI integration
3. **Implement Session Storage** - Persist sessions across restarts
4. **Add Streaming** - Use SSE (Server-Sent Events) for real-time responses
5. **Handle Tools** - Implement file operations and tool execution

See `/opencode-tui-adapter/README.md` for more details.

---

## Deployment Checklist

- [ ] Install Python 3.10+
- [ ] Install `uv` package manager
- [ ] Install Go 1.24.x
- [ ] Navigate to `opencode-tui-adapter/`
- [ ] Start adapter: `uv run python src/opencode_tui_adapter/server.py`
- [ ] Verify adapter at http://localhost:3000
- [ ] Run `python3 rebrand-helios.py` from repo root
- [ ] Build TUI: `cd packages/tui && go build -o helios ./cmd/opencode`
- [ ] Set `HELIOS_SERVER=http://localhost:3000`
- [ ] Run `./helios`
- [ ] Watch adapter logs for TUI interactions

---

## Architecture Diagram

```
┌─────────────────┐
│   Helios TUI    │  (Rebranded OpenCode TUI)
│   (Go Binary)   │  - Sun logo & theme
└────────┬────────┘  - Runs on your terminal
         │
         │ HTTP REST + SSE
         │ HELIOS_SERVER=http://localhost:3000
         │
┌────────▼────────┐
│ Adapter Server  │  (Your Python server)
│  (Port 3000)    │  - Logs all requests
└────────┬────────┘  - Returns dummy responses
         │           - Will integrate with CrewAI
         │
┌────────▼────────┐
│   Your Backend  │  (Future: CrewAI integration)
│    (CrewAI)     │
└─────────────────┘
```

---

## Common Workflows

### Testing Protocol Changes

When developing your adapter:

```bash
# Terminal 1: Run adapter with logs
cd opencode-tui-adapter
uv run python src/opencode_tui_adapter/server.py

# Terminal 2: Run Helios and interact
HELIOS_SERVER=http://localhost:3000 packages/tui/helios

# Watch Terminal 1 for detailed request/response logs
```

### Development Mode

For rapid iteration:

```bash
# Edit adapter code
# Ctrl+C to stop server
# Run again to test changes
uv run python src/opencode_tui_adapter/server.py
```

The TUI doesn't need rebuilding unless you change its code or rebranding.
