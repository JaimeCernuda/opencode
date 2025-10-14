#!/usr/bin/env python3
"""
iowarp - Single command to start both the logging server and TUI
"""
import subprocess
import sys
import time
import os
import signal
from pathlib import Path

def find_project_root():
    """Find the opencode project root"""
    current = Path(__file__).parent
    # Go up one level to find the opencode root
    return current.parent

def find_tui_binary():
    """Find or build the TUI binary"""
    root = find_project_root()
    tui_dir = root / "packages" / "tui" / "cmd" / "opencode"

    # Check for existing binary
    if sys.platform == "win32":
        binary_name = "tui.exe"
    else:
        binary_name = "tui"

    binary_path = tui_dir / binary_name

    if binary_path.exists():
        print(f"✅ Found TUI binary: {binary_path}")
        return binary_path

    # Build it
    print(f"🔨 Building TUI binary...")
    print(f"   Directory: {tui_dir}")

    if not tui_dir.exists():
        print(f"❌ TUI directory not found: {tui_dir}")
        sys.exit(1)

    try:
        result = subprocess.run(
            ["go", "build", "-o", binary_name, "main.go"],
            cwd=tui_dir,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"❌ Build failed:")
            print(result.stderr)
            sys.exit(1)

        print(f"✅ Built TUI binary: {binary_path}")
        return binary_path

    except FileNotFoundError:
        print("❌ Go not found. Please install Go: https://golang.org/dl/")
        sys.exit(1)

def main():
    print("\n" + "="*80)
    print("🚀 iowarp - OpenCode TUI Logging Adapter")
    print("="*80 + "\n")

    # Find paths
    adapter_dir = Path(__file__).parent
    server_script = adapter_dir / "src" / "opencode_tui_adapter" / "server.py"

    if not server_script.exists():
        print(f"❌ Server script not found: {server_script}")
        sys.exit(1)

    # Find/build TUI
    tui_binary = find_tui_binary()

    # Start server process
    print("\n📡 Starting logging server...")
    server_process = subprocess.Popen(
        [sys.executable, str(server_script)],
        cwd=adapter_dir
    )

    # Give server time to start
    print("⏳ Waiting for server to initialize...")
    time.sleep(2)

    # Check if server is still running
    if server_process.poll() is not None:
        print("❌ Server failed to start")
        sys.exit(1)

    print("✅ Server started on http://localhost:3000\n")

    # Start TUI process
    print("🖥️  Starting TUI...\n")
    print("="*80 + "\n")

    env = os.environ.copy()
    env["OPENCODE_SERVER"] = "http://localhost:3000"

    tui_process = subprocess.Popen(
        [str(tui_binary)],
        env=env
    )

    # Handle cleanup
    def cleanup(signum=None, frame=None):
        print("\n\n" + "="*80)
        print("🛑 Shutting down...")
        print("="*80)

        print("   Stopping TUI...")
        try:
            tui_process.terminate()
            tui_process.wait(timeout=5)
        except:
            tui_process.kill()

        print("   Stopping server...")
        try:
            server_process.terminate()
            server_process.wait(timeout=5)
        except:
            server_process.kill()

        print("✅ Clean shutdown complete\n")
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        # Wait for TUI to exit
        tui_process.wait()

        # If TUI exits, clean up server
        print("\n🖥️  TUI exited")
        cleanup()

    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
