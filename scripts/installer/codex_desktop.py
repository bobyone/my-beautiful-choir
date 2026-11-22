# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Register personal mode in ChatGPT desktop through the local Codex CLI."""

import json
from collections.abc import Callable
from pathlib import Path

from scripts.installer.client import SERVER_NAME, ClientRegistration
from scripts.installer.errors import InstallationError
from scripts.installer.launcher import Launcher
from scripts.installer.process import run_command


class CodexDesktopRegistration(ClientRegistration):
    """Use Codex's own commands to preserve unrelated configuration."""

    def __init__(self, codex: Path) -> None:
        self._codex = codex

    def _current(self) -> dict[str, object] | None:
        output = run_command(
            [str(self._codex), "mcp", "get", SERVER_NAME, "--json"],
            failure="Codex could not check the MCP registration. Check that the CLI is available.",
            missing_message=f"Error: No MCP server named '{SERVER_NAME}' found.",
        )
        if output is None:
            return None
        try:
            entry = json.loads(output)
        except ValueError as error:
            raise InstallationError("Codex returned an unreadable MCP registration.") from error
        if not isinstance(entry, dict) or entry.get("name") != SERVER_NAME:
            raise InstallationError("Codex returned an unexpected MCP registration.")
        return entry

    def register(self, launcher: Launcher, confirm_replace: Callable[[], bool]) -> None:
        """Keep an identical registration or add it using the supported CLI."""
        command, *args = launcher.command
        entry = self._current()
        if entry is not None:
            transport = entry.get("transport")
            if (
                entry.get("enabled", True) is True
                and isinstance(transport, dict)
                and transport.get("type") == "stdio"
                and transport.get("command") == command
                and transport.get("args") == args
                and transport.get("cwd") is None
                and not transport.get("env")
                and not transport.get("env_vars")
            ):
                return
            if not confirm_replace():
                raise InstallationError("The existing Codex registration was kept.")
            if self._current() != entry:
                raise InstallationError("The Codex registration changed. Run the installer again.")

        run_command(
            [str(self._codex), "mcp", "add", SERVER_NAME, "--", command, *args],
            failure="Codex could not register the server. Check its MCP settings.",
        )
