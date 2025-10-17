#!/usr/bin/env python3
"""
Helios Rebranding Script
========================
Rebrand OpenCode TUI to Helios with sun imagery.

Usage:
    python rebrand-helios.py              # Apply rebranding
    python rebrand-helios.py --dry-run    # Preview changes without applying
    python rebrand-helios.py --revert     # Revert to original (requires git)

This script is designed to be run before building/deploying to maintain
upstream sync while applying custom branding.
"""

import re
import sys
import json
import shutil
from pathlib import Path
from typing import List, Tuple, Optional

# Configuration
REPO_ROOT = Path(__file__).parent
TUI_PATH = REPO_ROOT / "packages" / "tui"

# Helios branding assets
HELIOS_LOGO = '''  ╦ ╦╔═╗╦  ╦╔═╗╔═╗
  ╠═╣║╣ ║  ║║ ║╚═╗
  ╩ ╩╚═╝╩═╝╩╚═╝╚═╝'''

HELIOS_SUN_LOGO = (
    "    \\   |   /\n"
    "     '.  '  .'\n"
    "   -- (     ) --\n"
    "     .'  '  '.\n"
    "    /   |   \\"
)

HELIOS_LOADING_SUN = (
    "       .''.\n"
    "     .'  _  '.\n"
    "    /  .' '.  \\\n"
    "   |  /  _  \\  |\n"
    "   | |  / \\  | |\n"
    "    \\|  \\_/  |/\n"
    "     \\  '.'  /\n"
    "      '.___.'\n"
    "   ───── ☀ ─────"
)

# Helios theme colors (sun-inspired: warm oranges, yellows, golds)
HELIOS_THEME = {
    "name": "helios",
    "colors": {
        "dark": {
            "background-1": "#1a1410",
            "background-2": "#2a2218",
            "background-3": "#3a3020",
            "text": "#f5e6d3",
            "textMuted": "#c4a57b",
            "base": "#ff9933",
            "primary": "#ffaa44",
            "secondary": "#ffcc66",
            "error": "#ff4444",
            "warning": "#ffaa00",
            "success": "#88cc44",
            "info": "#66aaff",
            "diffAdded": "#88cc44",
            "diffRemoved": "#ff4444",
            "diffContext": "#666666",
            "diffAddedHighlight": "#44ff44",
            "diffRemovedHighlight": "#ff0000",
            "markdownLink": "#66aaff",
            "markdownCode": "#ffcc66",
            "markdownStrong": "#ffaa44",
            "markdownEmphasis": "#ff9933",
            "markdownH1": "#ffaa44",
            "markdownH2": "#ff9933",
            "markdownH3": "#cc7722",
            "syntaxKeyword": "#ff9933",
            "syntaxString": "#ffcc66",
            "syntaxNumber": "#ffaa44",
            "syntaxComment": "#8a7a5a",
            "syntaxFunction": "#ff9933",
            "syntaxType": "#ffaa44"
        },
        "light": {
            "background-1": "#fffef8",
            "background-2": "#faf8f0",
            "background-3": "#f5f0e8",
            "text": "#2a2010",
            "textMuted": "#6a5a3a",
            "base": "#cc7722",
            "primary": "#dd8833",
            "secondary": "#ee9944",
            "error": "#cc3333",
            "warning": "#dd7700",
            "success": "#55aa22",
            "info": "#3388dd",
            "diffAdded": "#55aa22",
            "diffRemoved": "#cc3333",
            "diffContext": "#999999",
            "diffAddedHighlight": "#33ff33",
            "diffRemovedHighlight": "#ff0000",
            "markdownLink": "#3388dd",
            "markdownCode": "#ee9944",
            "markdownStrong": "#dd8833",
            "markdownEmphasis": "#cc7722",
            "markdownH1": "#dd8833",
            "markdownH2": "#cc7722",
            "markdownH3": "#aa5511",
            "syntaxKeyword": "#cc7722",
            "syntaxString": "#ee9944",
            "syntaxNumber": "#dd8833",
            "syntaxComment": "#8a7a5a",
            "syntaxFunction": "#cc7722",
            "syntaxType": "#dd8833"
        }
    }
}


class Rebrander:
    """Handles rebranding operations."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.changes: List[Tuple[Path, str, str]] = []

    def log(self, message: str, prefix: str = ""):
        """Log a message."""
        if prefix:
            print(f"{prefix} {message}")
        else:
            print(message)

    def replace_in_file(
        self,
        file_path: Path,
        pattern: str,
        replacement: str,
        regex: bool = False,
        description: str = ""
    ) -> bool:
        """Replace text in a file."""
        if not file_path.exists():
            self.log(f"⚠️  File not found: {file_path}", "")
            return False

        content = file_path.read_text(encoding='utf-8')
        original = content

        if regex:
            content = re.sub(pattern, replacement, content)
        else:
            content = content.replace(pattern, replacement)

        if content != original:
            self.changes.append((file_path, original, content))

            if self.dry_run:
                self.log(f"Would modify: {file_path.relative_to(REPO_ROOT)}", "📝")
                if description:
                    self.log(f"  → {description}", "")
            else:
                file_path.write_text(content, encoding='utf-8')
                self.log(f"Modified: {file_path.relative_to(REPO_ROOT)}", "✓")
                if description:
                    self.log(f"  → {description}", "")
            return True
        return False

    def rebrand_logo(self):
        """Replace OpenCode logo with Helios logo."""
        self.log("\n🎨 Rebranding logo...", "")

        logo_file = TUI_PATH / "internal" / "tui" / "tui.go"

        # Match the actual logo structure in tui.go
        # This includes base/muted variable declarations, the `open` and `code` backtick strings, and the JoinHorizontal call
        old_logo_pattern = r'base := baseStyle\.Render\s*\n\s*muted := styles\.NewStyle\(\)\.Foreground\(t\.TextMuted\(\)\)\.Background\(t\.Background\(\)\)\.Render\s*\n\s*open := `[^`]*`\s*\n\s*code := `[^`]*`\s*\n\s*logo := lipgloss\.JoinHorizontal\(\s*lipgloss\.Top,\s*muted\(open\),\s*base\(code\),\s*\)'

        # Create the new Helios logo code (without muted variable to avoid unused variable error)
        new_logo_code = f'''base := baseStyle.Render

\thelios := `{HELIOS_LOGO}`

\tlogo := lipgloss.JoinVertical(
\t\tlipgloss.Left,
\t\tbase(helios),
\t)'''

        self.replace_in_file(
            logo_file,
            old_logo_pattern,
            new_logo_code,
            regex=True,
            description="Replace OpenCode logo with Helios logo"
        )

    def rebrand_loading_screen(self):
        """Add sun imagery to loading screen."""
        self.log("\n☀️  Adding sun loading screen...", "")

        messages_file = TUI_PATH / "internal" / "components" / "chat" / "messages.go"

        # Replace the loading screen (lines 1046-1054)
        old_loading = r'if m\.loading \{\s*return lipgloss\.Place\(\s*m\.width,\s*m\.height,\s*lipgloss\.Center,\s*lipgloss\.Center,\s*styles\.NewStyle\(\)\.Background\(bgColor\)\.Render\(""\),\s*styles\.WhitespaceStyle\(bgColor\),\s*\)\s*\}'

        loading_art = HELIOS_LOADING_SUN.replace('\n', '\\n')

        new_loading = f'''if m.loading {{
\t\tloadingArt := `{HELIOS_LOADING_SUN}`
\t\treturn lipgloss.Place(
\t\t\tm.width,
\t\t\tm.height,
\t\t\tlipgloss.Center,
\t\t\tlipgloss.Center,
\t\t\tstyles.NewStyle().Foreground(t.Primary()).Background(bgColor).Render(loadingArt),
\t\t\tstyles.WhitespaceStyle(bgColor),
\t\t)
\t}}'''

        self.replace_in_file(
            messages_file,
            old_loading,
            new_loading,
            regex=True,
            description="Add Helios sun to loading screen"
        )

    def rebrand_status_bar(self):
        """Update status bar branding."""
        self.log("\n📊 Updating status bar...", "")

        status_file = TUI_PATH / "internal" / "components" / "status" / "status.go"

        # Replace "opencode" with "helios" in status bar
        self.replace_in_file(
            status_file,
            'return "opencode " + s.version',
            'return "helios " + s.version',
            description="Update status bar text"
        )

    def rebrand_binary_name(self):
        """Update binary and package names."""
        self.log("\n📦 Updating binary names...", "")

        # Update main.go
        main_file = TUI_PATH / "cmd" / "opencode" / "main.go"

        # Update app name
        self.replace_in_file(
            main_file,
            'Name: "opencode"',
            'Name: "helios"',
            description="Update app name in main.go"
        )

        # Update CLI usage text if present
        self.replace_in_file(
            main_file,
            'opencode TUI',
            'helios TUI',
            description="Update TUI reference"
        )

    def create_helios_theme(self):
        """Create Helios theme file."""
        self.log("\n🎨 Creating Helios theme...", "")

        theme_dir = TUI_PATH / "internal" / "theme" / "themes"
        theme_file = theme_dir / "helios.json"

        if self.dry_run:
            self.log(f"Would create: {theme_file.relative_to(REPO_ROOT)}", "📝")
        else:
            theme_dir.mkdir(parents=True, exist_ok=True)
            with open(theme_file, 'w', encoding='utf-8') as f:
                json.dump(HELIOS_THEME, f, indent=2)
            self.log(f"Created: {theme_file.relative_to(REPO_ROOT)}", "✓")

    def update_environment_references(self):
        """Update environment variable references."""
        self.log("\n🌍 Updating environment variables...", "")

        # Find all Go files that reference OPENCODE_ env vars
        go_files = list(TUI_PATH.rglob("*.go"))

        for go_file in go_files:
            # Replace OPENCODE_THEME with HELIOS_THEME
            self.replace_in_file(
                go_file,
                'OPENCODE_THEME',
                'HELIOS_THEME',
                description=f"Update env var in {go_file.name}"
            )

            # Replace OPENCODE_SERVER with HELIOS_SERVER
            self.replace_in_file(
                go_file,
                'OPENCODE_SERVER',
                'HELIOS_SERVER',
                description=f"Update server env var in {go_file.name}"
            )

    def update_config_paths(self):
        """Update config directory paths - only in string literals, not import paths."""
        self.log("\n📁 Updating config directory paths...", "")

        # Only update specific config path strings, not import paths
        # Target files that contain config directory references
        config_files = [
            TUI_PATH / "internal" / "theme" / "loader.go",
            TUI_PATH / "internal" / "app" / "app.go",
        ]

        for config_file in config_files:
            if not config_file.exists():
                continue

            # Replace config directory names in string literals only
            # Look for patterns like "/opencode/themes" and ".opencode/themes"
            self.replace_in_file(
                config_file,
                '"/opencode/',
                '"/helios/',
                regex=False,
                description=f"Update config dir in {config_file.name}"
            )

            self.replace_in_file(
                config_file,
                '".opencode',
                '".helios',
                regex=False,
                description=f"Update dotfile dir in {config_file.name}"
            )

    def update_comments_and_docs(self):
        """Update comments and documentation - ONLY in user-facing strings."""
        self.log("\n📚 Updating user-facing strings in comments...", "")

        go_files = list(TUI_PATH.rglob("*.go"))

        for go_file in go_files:
            content = go_file.read_text(encoding='utf-8')
            original = content

            # Only replace in comments (lines starting with //), not in code or imports
            lines = content.split('\n')
            modified = False
            for i, line in enumerate(lines):
                stripped = line.lstrip()
                # Only modify comments, not code
                if stripped.startswith('//'):
                    new_line = line.replace('OpenCode', 'Helios')
                    new_line = new_line.replace('opencode', 'helios')
                    if new_line != line:
                        lines[i] = new_line
                        modified = True

            if modified:
                content = '\n'.join(lines)
                if self.dry_run:
                    self.log(f"Would update comments in: {go_file.relative_to(REPO_ROOT)}", "📝")
                else:
                    go_file.write_text(content, encoding='utf-8')
                    self.log(f"Updated comments in: {go_file.relative_to(REPO_ROOT)}", "✓")

    def run(self):
        """Run all rebranding operations."""
        mode = "DRY RUN MODE" if self.dry_run else "APPLYING CHANGES"
        self.log(f"\n{'='*60}", "")
        self.log(f"🌞 HELIOS REBRANDING SCRIPT - {mode}", "")
        self.log(f"{'='*60}", "")

        # Execute all rebranding steps
        self.rebrand_logo()
        self.rebrand_loading_screen()
        self.rebrand_status_bar()
        self.rebrand_binary_name()
        self.create_helios_theme()
        self.update_environment_references()
        self.update_config_paths()
        self.update_comments_and_docs()

        # Summary
        self.log(f"\n{'='*60}", "")
        if self.dry_run:
            self.log("✨ Dry run complete! No files were modified.", "")
            self.log("   Run without --dry-run to apply changes.", "")
        else:
            self.log(f"✨ Rebranding complete! {len(self.changes)} files modified.", "")
            self.log("", "")
            self.log("Next steps:", "")
            self.log("  1. Review changes: git diff", "")
            self.log("  2. Build TUI: cd packages/tui && go build ./cmd/opencode", "")
            self.log("  3. Test: ./opencode", "")
        self.log(f"{'='*60}\n", "")


def revert_changes():
    """Revert changes using git."""
    print("\n🔄 Reverting changes...")

    import subprocess

    try:
        # Check if we're in a git repo
        subprocess.run(["git", "rev-parse", "--git-dir"],
                      check=True, capture_output=True, cwd=REPO_ROOT)

        # Revert changes to packages/tui
        subprocess.run(["git", "checkout", "HEAD", "packages/tui/"],
                      check=True, cwd=REPO_ROOT)

        print("✓ Changes reverted successfully!")
        print("  Run 'git status' to verify.")

    except subprocess.CalledProcessError:
        print("❌ Error: Not a git repository or git command failed.")
        print("   Please manually revert changes.")
        sys.exit(1)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Rebrand OpenCode TUI to Helios",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python rebrand-helios.py              Apply rebranding
  python rebrand-helios.py --dry-run    Preview changes
  python rebrand-helios.py --revert     Revert to original
        """
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files"
    )

    parser.add_argument(
        "--revert",
        action="store_true",
        help="Revert changes using git"
    )

    args = parser.parse_args()

    if args.revert:
        revert_changes()
        return

    # Verify we're in the right place
    if not TUI_PATH.exists():
        print(f"❌ Error: TUI path not found: {TUI_PATH}")
        print("   Make sure you're running this from the opencode repository root.")
        sys.exit(1)

    # Run rebranding
    rebrander = Rebrander(dry_run=args.dry_run)
    rebrander.run()


if __name__ == "__main__":
    main()
