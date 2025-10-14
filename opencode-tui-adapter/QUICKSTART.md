# Quick Start Guide

## Easy Mode: One Command

```bash
cd opencode-tui-adapter
uv run python iowarp.py
```

This will:
1. ✅ Build the TUI if needed
2. ✅ Start the logging server
3. ✅ Launch the TUI connected to the server
4. ✅ Clean up everything when you exit (Ctrl+C)

**That's it!** Watch the terminal for detailed request logs.

---

## Manual Mode (if you prefer)

### 1. Start the Logging Server

```bash
cd opencode-tui-adapter
uv run python src/opencode_tui_adapter/server.py
```

Expected output:
```
================================================================================
🚀 OpenCode TUI Logging Server Starting...
================================================================================
```

Server will be running at `http://localhost:3000`

---

## 2. Build the Go TUI (First Time Only)

Open a **new terminal**:

```bash
cd packages/tui/cmd/opencode
go build -o tui.exe main.go
```

---

## 3. Connect the TUI to Your Server

**Windows PowerShell:**
```powershell
cd packages/tui/cmd/opencode
$env:OPENCODE_SERVER="http://localhost:3000"
.\tui.exe
```

**Windows CMD:**
```cmd
cd packages\tui\cmd\opencode
set OPENCODE_SERVER=http://localhost:3000
tui.exe
```

**Linux/Mac:**
```bash
cd packages/tui/cmd/opencode
OPENCODE_SERVER=http://localhost:3000 ./tui
```

---

## 4. Test It!

In the TUI:
1. Type a message and press Enter
2. Watch the server terminal - you'll see detailed logs!

Example server output:
```
🚀 🚀 🚀 MESSAGE RECEIVED for session: sess_123 🚀 🚀 🚀

📋 Message Details:
   Message ID: msg_789
   Agent: test-agent
   Model: test/test-model

📦 Parts (1):
   Part 1:
      Type: text
      Text: Hello world
```

---

## Troubleshooting

**TUI can't connect:**
- Make sure server is running on port 3000
- Check firewall settings
- Verify `OPENCODE_SERVER` environment variable is set

**Go build fails:**
- Ensure Go is installed: `go version`
- Run `go mod download` in the tui directory

**Python/uv issues:**
- Ensure Python 3.10+ is installed
- Ensure uv is installed: `uv --version`
- Try: `uv sync` in the adapter directory

---

## What's Next?

Once you see the logs working:
1. Understand the protocol from the logs
2. Replace dummy responses with CrewAI calls
3. Implement session persistence
4. Add streaming SSE events for real-time updates
