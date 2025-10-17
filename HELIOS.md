# Helios - OpenCode Complete System Launcher

Helios is a single-command launcher that sets up and runs the complete OpenCode system with both the TUI and backend adapter.

## What It Does

Helios automates the entire OpenCode setup and deployment process:

1. ✅ **Checks dependencies** (Go and uv)
2. 🔨 **Builds the TUI** from Go source
3. ⚙️  **Sets up the adapter server** with dependencies
4. 🚀 **Starts the backend server** in the background
5. 🌐 **Configures environment** (OPENCODE_SERVER variable)
6. 🖥️  **Launches the TUI** connected to the server

## Prerequisites

You need two tools installed:

- **Go** (1.24+): https://golang.org/dl/
- **uv**: https://github.com/astral-sh/uv

Helios will check for these and provide installation links if they're missing.

## Installation

### Option 1: Direct Execution

```bash
# Make executable
chmod +x helios.py

# Run directly
./helios.py
```

### Option 2: Using uv (Recommended)

From the project root (`/home/jcernuda/opencode-1/`):

```bash
# Run with uv
uv run helios

# Or if you prefer uvx
uvx --from . helios
```

## Usage

### Quick Start

```bash
# From the opencode-1 directory
uv run helios
```

That's it! Helios will:
- Check your system has Go and uv
- Build the TUI binary (if needed)
- Install adapter dependencies
- Start the backend server on port 3000
- Launch the TUI connected to the server

### What You'll See

```
================================================================================
🌟 HELIOS - OpenCode Complete System
================================================================================

================================================================================
🔍 Checking Dependencies
================================================================================

✅ Found go
✅ Found uv

✅ All dependencies found

📁 Project root: /home/jcernuda/opencode-1

================================================================================
🔨 Building TUI
================================================================================

   Source: /home/jcernuda/opencode-1/packages/tui/cmd/opencode
   Output: /home/jcernuda/opencode-1/packages/tui/helios

✅ TUI built successfully

================================================================================
⚙️  Setting Up Adapter Server
================================================================================

   Directory: /home/jcernuda/opencode-1/opencode-tui-adapter

   Installing dependencies...
✅ Dependencies installed

================================================================================
🚀 Starting Adapter Server
================================================================================

   Directory: /home/jcernuda/opencode-1/opencode-tui-adapter
   Server URL: http://localhost:3000

   Waiting for server to initialize...
✅ Server started successfully

================================================================================
🖥️  Starting TUI
================================================================================

   Binary: /home/jcernuda/opencode-1/packages/tui/helios
   Server: http://localhost:3000

================================================================================

[TUI starts here]
```

### Stopping Helios

Press `Ctrl+C` or exit the TUI. Helios will automatically:
- Stop the TUI process
- Stop the backend server
- Perform clean shutdown

```
================================================================================
🛑 Shutting Down
================================================================================

   Stopping TUI...
   Stopping server...
✅ Clean shutdown complete
```

## Environment Variables

Helios automatically sets:

- `OPENCODE_SERVER=http://localhost:3000` - Connects TUI to backend

You can also set these before running Helios:

```bash
# Use different port
export OPENCODE_PORT=3001
uv run helios

# Enable debug logging
export OPENCODE_LOG_LEVEL=DEBUG
uv run helios

# Use custom API key
export ANTHROPIC_API_KEY=sk-ant-...
uv run helios
```

## Project Structure

Helios expects this directory structure:

```
opencode-1/
├── helios.py                    # This launcher script
├── pyproject.toml               # uv configuration
├── packages/
│   └── tui/                     # Go TUI source
│       ├── cmd/opencode/
│       │   └── main.go
│       └── helios               # Built binary (created by helios)
└── opencode-tui-adapter/        # Python backend
    ├── pyproject.toml
    └── src/
```

## Troubleshooting

### "Go not found"

```
❌ go not found
   Install from: https://golang.org/dl/
```

**Solution**: Install Go from the provided link.

### "uv not found"

```
❌ uv not found
   Install from: https://github.com/astral-sh/uv
```

**Solution**: Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "Server failed to start"

Check the adapter directory exists and has correct dependencies:

```bash
cd opencode-tui-adapter
uv sync
uv run opencode-tui-adapter
```

Look for errors in the server output.

### "TUI build failed"

Check Go can build the TUI manually:

```bash
cd packages/tui/cmd/opencode
go build -o helios .
```

Check for missing dependencies:
```bash
cd packages/tui
go mod tidy
```

### Port Already in Use

If port 3000 is already in use:

```bash
# Use different port
export OPENCODE_PORT=3001
uv run helios
```

Or stop the process using port 3000:
```bash
lsof -ti:3000 | xargs kill
```

## Advanced Usage

### Manual Control

If you want more control, you can run components separately:

```bash
# Terminal 1: Start server manually
cd opencode-tui-adapter
export OPENCODE_LOG_LEVEL=DEBUG
uv run opencode-tui-adapter

# Terminal 2: Run TUI manually
cd packages/tui
export OPENCODE_SERVER=http://localhost:3000
./helios
```

### Development Mode

For development with auto-reload:

```bash
# Terminal 1: Run server with auto-reload
cd opencode-tui-adapter
uv run uvicorn opencode_tui_adapter.server:app --reload

# Terminal 2: Use helios for TUI only
# (modify helios.py to skip server startup)
```

### Custom Build Options

Edit `helios.py` to customize:

```python
# In build_tui() function
result = subprocess.run(
    ["go", "build", "-ldflags", "-s -w", "-o", str(binary_path), "."],
    #                ^^^^^^^^^^^^^^^^^^^ add build flags
    cwd=cmd_dir,
    capture_output=True,
    text=True,
)
```

## Integration with Other Tools

### With systemd (Linux)

Create `/etc/systemd/system/opencode.service`:

```ini
[Unit]
Description=OpenCode TUI System
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/opencode-1
ExecStart=/usr/bin/uv run helios
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable opencode
sudo systemctl start opencode
```

### With Docker

Create a `Dockerfile` in the root:

```dockerfile
FROM golang:1.24 AS tui-builder
WORKDIR /app
COPY packages/tui /app
RUN cd cmd/opencode && go build -o /helios .

FROM python:3.11
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
COPY --from=tui-builder /helios /usr/local/bin/helios
COPY opencode-tui-adapter /app/adapter
WORKDIR /app
COPY helios.py .
CMD ["uv", "run", "helios"]
```

## Comparison with iowarp.py

| Feature | iowarp.py | helios.py |
|---------|-----------|-----------|
| Dependency Check | ❌ No | ✅ Yes (Go + uv) |
| Error Messages | Basic | Detailed with URLs |
| Build Process | Basic | Robust with error handling |
| uv Support | ❌ No | ✅ Full uv integration |
| Entry Point | Direct script | uv run/uvx |
| Cleanup | Basic | Comprehensive |
| Documentation | Minimal | Extensive |

## Contributing

To modify helios:

1. Edit `helios.py`
2. Test changes:
   ```bash
   python3 helios.py
   ```
3. Test as uv entry point:
   ```bash
   uv run helios
   ```

## License

Same as OpenCode project.

## Support

For issues with helios:
1. Check this README
2. Check dependency installation
3. Run components manually to isolate the issue
4. Report bugs with full error output

---

**Happy coding with Helios!** 🌟
