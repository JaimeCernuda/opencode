"""
Helios - OpenCode TUI Adapter Launcher
Automatically sets up and launches the OpenCode TUI with the adapter backend.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


def check_claude_code_auth():
    """Check if Claude Code is authenticated."""
    # claude-agent-sdk uses Claude Code's existing OAuth authentication
    # No need to check for API key - it will use the logged-in Claude Code session
    print("✅ Using Claude Code authentication (OAuth)")


def check_claude_code_cli():
    """Check if Claude Code CLI is installed."""
    # Try both 'claude' and 'claude-code' commands
    for cmd in ["claude", "claude-code"]:
        try:
            subprocess.run(
                [cmd, "--version"],
                capture_output=True,
                check=True,
            )
            print(f"✅ Claude Code CLI found ({cmd})")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    print("❌ Claude Code CLI not found")
    print("\nPlease install it or ensure 'claude' is in your PATH")
    sys.exit(1)


def check_go_installed():
    """Check if Go is installed."""
    try:
        result = subprocess.run(
            ["go", "version"],
            capture_output=True,
            check=True,
            text=True,
        )
        version = result.stdout.strip()
        print(f"✅ Go found ({version})")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Go not found")
        print("\nPlease install Go 1.24.x or higher")
        sys.exit(1)


def build_tui_binary():
    """Build the OpenCode TUI from Go source."""
    print("\n🔨 Building OpenCode TUI from source...")

    # Find the TUI source directory (go up from helios.py to opencode-1 root)
    script_dir = Path(__file__).parent.parent.parent.parent  # 4 levels up
    tui_dir = script_dir / "packages" / "tui"

    if not tui_dir.exists():
        print(f"❌ TUI source directory not found: {tui_dir}")
        sys.exit(1)

    # Build the TUI binary
    try:
        subprocess.run(
            ["go", "build", "-o", "opencode", "./cmd/opencode"],
            cwd=str(tui_dir),
            check=True,
        )
        binary_path = tui_dir / "opencode"
        print(f"✅ TUI built successfully: {binary_path}")
        return binary_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build TUI: {e}")
        sys.exit(1)


def start_backend_server():
    """Start the FastAPI backend server in background."""
    print("\n🚀 Starting backend server...")

    # Get configuration
    host = os.environ.get("OPENCODE_SERVER_HOST", "127.0.0.1")
    port = os.environ.get("OPENCODE_SERVER_PORT", "3000")

    # Start server in background
    server_process = subprocess.Popen(
        ["uv", "run", "opencode-tui-adapter"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to be ready
    print(f"⏳ Waiting for server at http://{host}:{port}...")
    import socket
    for i in range(30):  # Try for 30 seconds
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, int(port)))
            sock.close()
            if result == 0:
                print(f"✅ Backend server ready at http://{host}:{port}")
                return server_process
        except:
            pass
        time.sleep(1)

    print("❌ Backend server failed to start")
    server_process.kill()
    sys.exit(1)


def start_tui_client(binary_path):
    """Start the OpenCode TUI client."""
    print("\n🎨 Starting OpenCode TUI...")

    # Set server URL for TUI (TUI expects HELIOS_SERVER env var)
    server_url = os.environ.get("HELIOS_SERVER", "http://127.0.0.1:3000")
    env = os.environ.copy()
    env["HELIOS_SERVER"] = server_url

    # Launch TUI
    try:
        subprocess.run([str(binary_path), "tui"], env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ TUI exited with error: {e}")
    except KeyboardInterrupt:
        print("\n⏸️  TUI interrupted by user")


def main():
    """Main launcher function."""
    print("=" * 60)
    print("🔆 HELIOS - OpenCode TUI Adapter Launcher")
    print("=" * 60)

    # Pre-flight checks
    print("\n📋 Pre-flight checks:")
    check_claude_code_auth()
    check_claude_code_cli()
    check_go_installed()

    # Build TUI from source
    tui_binary = build_tui_binary()

    # Start backend server
    server_process = start_backend_server()

    try:
        # Start TUI client
        start_tui_client(tui_binary)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
    finally:
        # Clean up server process
        if server_process:
            print("🧹 Stopping backend server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()

        print("👋 Goodbye!")


if __name__ == "__main__":
    main()
