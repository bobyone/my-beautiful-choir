# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Register personal mode in Claude Desktop's local MCP settings."""

import json
import stat
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from tempfile import NamedTemporaryFile

from scripts.installer.client import SERVER_NAME, ClientRegistration
from scripts.installer.errors import InstallationError
from scripts.installer.launcher import Launcher


class ClaudeDesktopRegistration(ClientRegistration):
    """Update one entry in Claude Desktop's JSON settings."""

    def __init__(self, config: Path) -> None:
        self._config = config

    @classmethod
    def for_current_user(
        cls, platform: str, environment: Mapping[str, str], home: Path
    ) -> "ClaudeDesktopRegistration":
        """Resolve the platform's default settings location without reading it."""
        if platform == "win32" and (app_data := environment.get("APPDATA")):
            directory = Path(app_data) / "Claude"
        elif platform == "darwin":
            directory = home / "Library" / "Application Support" / "Claude"
        else:
            raise InstallationError("Claude Desktop setup requires Windows or macOS.")
        if not directory.is_dir():
            raise InstallationError("Install and open Claude Desktop once, then retry.")
        return cls(directory / "claude_desktop_config.json")

    def _read_source(self) -> str | None:
        if self._config.is_symlink():
            raise InstallationError("Claude Desktop's settings file is a symbolic link.")
        try:
            return self._config.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None

    def register(self, launcher: Launcher, confirm_replace: Callable[[], bool]) -> None:
        """Keep unrelated JSON values and publish a complete replacement atomically."""
        command, *args = launcher.command
        wanted = {"command": command, "args": args}
        try:
            source = self._read_source()
            config = {} if source is None else json.loads(source.removeprefix("\ufeff"))
            if not isinstance(config, dict):
                raise InstallationError("Claude Desktop's settings must contain a JSON object.")
            servers = config.setdefault("mcpServers", {})
            if not isinstance(servers, dict):
                raise InstallationError("Claude Desktop's mcpServers setting must be an object.")

            if servers.get(SERVER_NAME) == wanted:
                return
            if SERVER_NAME in servers and not confirm_replace():
                raise InstallationError("The existing Claude Desktop registration was kept.")
            servers[SERVER_NAME] = wanted
            self._write(config, source)
        except (OSError, ValueError) as error:
            raise InstallationError(
                "Claude Desktop's settings could not be updated. Check the JSON and file access."
            ) from error

    def _write(self, config: dict[str, object], source: str | None) -> None:
        temporary: Path | None = None
        try:
            with NamedTemporaryFile(
                dir=self._config.parent, delete=False, mode="w", encoding="utf-8", newline="\n"
            ) as stream:
                temporary = Path(stream.name)
                json.dump(config, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            if source is not None and sys.platform != "win32":
                current_mode = stat.S_IMODE(self._config.stat().st_mode)
                temporary.chmod(current_mode & 0o600)
            if self._read_source() != source:
                raise InstallationError(
                    "Claude Desktop's settings changed. Run the installer again."
                )
            temporary.replace(self._config)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
