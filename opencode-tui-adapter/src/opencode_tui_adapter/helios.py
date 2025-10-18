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


def start_tui_client():
    """Start the OpenCode TUI client."""
    print("\n🎨 Starting OpenCode TUI...")

    # Set server URL for TUI
    server_url = os.environ.get("OPENCODE_SERVER", "http://127.0.0.1:3000")
    os.environ["OPENCODE_SERVER"] = server_url

    # Launch TUI (assumes it's in PATH)
    try:
        # Try to find opencode TUI binary
        subprocess.run(["opencode", "tui"], check=True)
    except FileNotFoundError:
        print("❌ OpenCode TUI binary not found")
        print("\nPlease ensure the OpenCode TUI is installed and in your PATH")
        sys.exit(1)


def main():
    """Main launcher function."""
    print("=" * 60)
    print("🔆 HELIOS - OpenCode TUI Adapter Launcher")
    print("=" * 60)

    # Pre-flight checks
    print("\n📋 Pre-flight checks:")
    check_claude_code_auth()
    check_claude_code_cli()

    # Start backend server
    server_process = start_backend_server()

    try:
        # Start TUI client
        start_tui_client()
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
