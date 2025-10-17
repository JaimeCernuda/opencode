#!/usr/bin/env python3
"""
helios - Complete OpenCode setup and deployment script
Checks dependencies, builds components, and launches the complete system.
"""
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path


def check_command(command: str, install_url: str) -> bool:
    """Check if a command exists in PATH."""
    if shutil.which(command):
        print(f"✅ Found {command}")
        return True
    else:
        print(f"❌ {command} not found")
        print(f"   Install from: {install_url}")
        return False


def check_dependencies() -> bool:
    """Check all required dependencies."""
    print("\n" + "=" * 80)
    print("🔍 Checking Dependencies")
    print("=" * 80 + "\n")

    all_ok = True

    # Check Go
    if not check_command("go", "https://golang.org/dl/"):
        all_ok = False

    # Check uv
    if not check_command("uv", "https://github.com/astral-sh/uv"):
        all_ok = False

    if not all_ok:
        print("\n❌ Missing required dependencies. Please install them and try again.")
        return False

    print("\n✅ All dependencies found")
    return True


def find_project_root() -> Path:
    """Find the opencode project root."""
    # helios.py is in the root of opencode-1
    return Path(__file__).parent.absolute()


def build_tui(root: Path) -> Path:
    """Build the TUI binary using Go."""
    print("\n" + "=" * 80)
    print("🔨 Building TUI")
    print("=" * 80 + "\n")

    tui_dir = root / "packages" / "tui"
    cmd_dir = tui_dir / "cmd" / "opencode"

    if not cmd_dir.exists():
        print(f"❌ TUI source directory not found: {cmd_dir}")
        sys.exit(1)

    # Determine binary name based on platform
    if sys.platform == "win32":
        binary_name = "helios.exe"
    else:
        binary_name = "helios"

    binary_path = tui_dir / binary_name

    print(f"   Source: {cmd_dir}")
    print(f"   Output: {binary_path}")
    print()

    try:
        # Build from the cmd/opencode directory
        result = subprocess.run(
            ["go", "build", "-o", str(binary_path), "."],
            cwd=cmd_dir,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print("❌ TUI build failed:")
            print(result.stderr)
            sys.exit(1)

        print(f"✅ TUI built successfully: {binary_path}")
        return binary_path

    except Exception as e:
        print(f"❌ Error building TUI: {e}")
        sys.exit(1)


def setup_adapter(root: Path) -> Path:
    """Setup the OpenCode adapter server using uv."""
    print("\n" + "=" * 80)
    print("⚙️  Setting Up Adapter Server")
    print("=" * 80 + "\n")

    adapter_dir = root / "opencode-tui-adapter"

    if not adapter_dir.exists():
        print(f"❌ Adapter directory not found: {adapter_dir}")
        sys.exit(1)

    print(f"   Directory: {adapter_dir}")
    print()

    # Check if dependencies are installed
    print("   Installing dependencies...")
    try:
        result = subprocess.run(
            ["uv", "sync"],
            cwd=adapter_dir,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print("❌ Dependency installation failed:")
            print(result.stderr)
            sys.exit(1)

        print("✅ Dependencies installed")

    except Exception as e:
        print(f"❌ Error setting up adapter: {e}")
        sys.exit(1)

    return adapter_dir


def start_server(adapter_dir: Path) -> subprocess.Popen:
    """Start the adapter server in the background."""
    print("\n" + "=" * 80)
    print("🚀 Starting Adapter Server")
    print("=" * 80 + "\n")

    print(f"   Directory: {adapter_dir}")
    print(f"   Server URL: http://localhost:3000")
    print()

    try:
        # Start server with uv run
        server_process = subprocess.Popen(
            ["uv", "run", "opencode-tui-adapter"],
            cwd=adapter_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to start
        print("   Waiting for server to initialize...")
        time.sleep(3)

        # Check if server is still running
        if server_process.poll() is not None:
            print("❌ Server failed to start")
            # Print any output
            stdout, stderr = server_process.communicate()
            if stdout:
                print("STDOUT:", stdout.decode())
            if stderr:
                print("STDERR:", stderr.decode())
            sys.exit(1)

        print("✅ Server started successfully")
        return server_process

    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)


def start_tui(tui_binary: Path) -> subprocess.Popen:
    """Start the TUI with the correct environment."""
    print("\n" + "=" * 80)
    print("🖥️  Starting TUI")
    print("=" * 80 + "\n")

    # Set environment variable to connect to server
    env = os.environ.copy()
    env["OPENCODE_SERVER"] = "http://localhost:3000"

    print(f"   Binary: {tui_binary}")
    print(f"   Server: {env['OPENCODE_SERVER']}")
    print()
    print("=" * 80 + "\n")

    try:
        tui_process = subprocess.Popen(
            [str(tui_binary)],
            env=env,
        )

        return tui_process

    except Exception as e:
        print(f"❌ Error starting TUI: {e}")
        sys.exit(1)


def cleanup(server_process: subprocess.Popen, tui_process: subprocess.Popen = None):
    """Clean shutdown of all processes."""
    print("\n\n" + "=" * 80)
    print("🛑 Shutting Down")
    print("=" * 80 + "\n")

    if tui_process:
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


def main():
    """Main entry point for helios."""
    print("\n" + "=" * 80)
    print("🌟 HELIOS - OpenCode Complete System")
    print("=" * 80 + "\n")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Find project root
    root = find_project_root()
    print(f"\n📁 Project root: {root}")

    # Build TUI
    tui_binary = build_tui(root)

    # Setup adapter
    adapter_dir = setup_adapter(root)

    # Start server
    server_process = start_server(adapter_dir)

    # Setup signal handlers for clean shutdown
    def signal_handler(signum, frame):
        cleanup(server_process)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start TUI
    tui_process = start_tui(tui_binary)

    try:
        # Wait for TUI to exit
        tui_process.wait()

        # If TUI exits, clean up
        print("\n🖥️  TUI exited")
        cleanup(server_process)

    except KeyboardInterrupt:
        cleanup(server_process, tui_process)


if __name__ == "__main__":
    main()
