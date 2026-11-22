# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Install the local MCP server for ChatGPT desktop via Codex."""

import sys
from pathlib import Path

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.installer.cli import main
from scripts.installer.codex_desktop import CodexDesktopRegistration
from scripts.installer.process import executable

if __name__ == "__main__":
    raise SystemExit(
        main(
            "ChatGPT desktop (local Codex)",
            lambda environment: CodexDesktopRegistration(
                executable("codex", environment.get("PATH"))
            ),
        )
    )
