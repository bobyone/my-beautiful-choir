# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests for Codex registration through its supported CLI."""

import json
from pathlib import Path

import pytest
from scripts.installer.errors import InstallationError
from scripts.installer.launcher import Launcher

from scripts.installer import codex_desktop


def test_registration_and_rerun_through_the_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    launcher = Launcher(tmp_path / "uv", tmp_path / "choir project")
    codex = tmp_path / "codex"
    current: str | None = None
    commands: list[list[str]] = []

    def run(command: list[str], **options: object) -> str | None:
        nonlocal current
        commands.append(command)
        if command[2] == "get":
            return current
        assert command == [str(codex), "mcp", "add", "my-beautiful-choir", "--", *launcher.command]
        executable, *args = launcher.command
        current = json.dumps(
            {
                "name": "my-beautiful-choir",
                "enabled": True,
                "transport": {"type": "stdio", "command": executable, "args": args},
            }
        )
        return ""

    monkeypatch.setattr(codex_desktop, "run_command", run)
    client = codex_desktop.CodexDesktopRegistration(codex)
    client.register(launcher, lambda: pytest.fail("No conflict"))
    client.register(launcher, lambda: pytest.fail("No conflict"))
    assert [command[2] for command in commands] == ["get", "add", "get"]


def test_conflicting_or_invalid_registration_is_left_intact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = '{"name":"my-beautiful-choir","transport":{"type":"streamable_http"}}'

    def run(command: list[str], **options: object) -> str:
        assert command[2] == "get"
        return result

    monkeypatch.setattr(codex_desktop, "run_command", run)
    client = codex_desktop.CodexDesktopRegistration(tmp_path / "codex")
    launcher = Launcher(tmp_path / "uv", tmp_path)
    with pytest.raises(InstallationError, match="registration was kept"):
        client.register(launcher, lambda: False)
    result = "{broken"
    with pytest.raises(InstallationError, match="unreadable"):
        client.register(launcher, lambda: True)
