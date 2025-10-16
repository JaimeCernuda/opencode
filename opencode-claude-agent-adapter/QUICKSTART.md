# Quick Start Guide

Get up and running with OpenCode Claude Agent Adapter in 5 minutes!

## TL;DR - 3 Commands to Get Started

```bash
# 1. Install
cd opencode-claude-agent-adapter
uv pip install -e .

# 2. Run server (set API key in environment or .env file)
export ANTHROPIC_API_KEY=sk-ant-your-key-here  # Optional: only needed when sending messages
uv run python src/opencode_claude_agent/server.py

# 3. In NEW terminal, run TUI
export OPENCODE_SERVER=http://localhost:3000
./tui  # (wherever your OpenCode TUI binary is)
```
