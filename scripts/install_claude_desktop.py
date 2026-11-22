# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Install the local MCP server for Claude Desktop."""

import sys
from pathlib import Path

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.installer.claude_desktop import ClaudeDesktopRegistration
from scripts.installer.cli import main

if __name__ == "__main__":
    raise SystemExit(
        main(
            "Claude Desktop",
            lambda environment: ClaudeDesktopRegistration.for_current_user(
                sys.platform, environment, Path.home()
            ),
        )
    )
