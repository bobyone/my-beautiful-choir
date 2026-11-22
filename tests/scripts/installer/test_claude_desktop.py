# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests for Claude Desktop registration using temporary settings."""

import json
from pathlib import Path

import pytest
from scripts.installer.claude_desktop import ClaudeDesktopRegistration
from scripts.installer.errors import InstallationError
from scripts.installer.launcher import Launcher


def test_preserves_other_settings_and_keeps_an_identical_registration(tmp_path: Path) -> None:
    path = tmp_path / "claude_desktop_config.json"
    original = {"preferences": {"theme": "dark"}, "mcpServers": {"other": {"command": "other"}}}
    path.write_text(json.dumps(original), encoding="utf-8")
    launcher = Launcher(tmp_path / "uv", tmp_path / "a clone with spaces")
    registration = ClaudeDesktopRegistration(path)

    registration.register(launcher, lambda: pytest.fail("No conflict"))
    installed = path.read_text(encoding="utf-8")
    data = json.loads(installed)
    assert data["preferences"] == original["preferences"]
    assert data["mcpServers"]["other"] == {"command": "other"}
    assert data["mcpServers"]["my-beautiful-choir"] == {
        "command": launcher.command[0],
        "args": list(launcher.command[1:]),
    }

    unchanged = installed.replace("  ", "    ")
    path.write_text(unchanged, encoding="utf-8")
    registration.register(launcher, lambda: pytest.fail("No conflict"))
    assert path.read_text(encoding="utf-8") == unchanged


def test_new_config_and_explicit_conflict_replacement(tmp_path: Path) -> None:
    path = tmp_path / "claude_desktop_config.json"
    registration = ClaudeDesktopRegistration(path)
    registration.register(Launcher(tmp_path / "uv", tmp_path / "first"), lambda: False)
    previous = path.read_bytes()
    replacement = Launcher(tmp_path / "uv", tmp_path / "second")

    with pytest.raises(InstallationError, match="registration was kept"):
        registration.register(replacement, lambda: False)
    assert path.read_bytes() == previous

    registration.register(replacement, lambda: True)
    current = json.loads(path.read_text(encoding="utf-8"))
    assert current["mcpServers"]["my-beautiful-choir"]["args"] == list(replacement.command[1:])


def test_preserves_a_settings_change_made_during_confirmation(tmp_path: Path) -> None:
    path = tmp_path / "claude_desktop_config.json"
    path.write_text('{"mcpServers":{"my-beautiful-choir":{"command":"old"}}}', encoding="utf-8")
    later = '{"preferences":{"theme":"light"}}'

    def approve() -> bool:
        path.write_text(later, encoding="utf-8")
        return True

    with pytest.raises(InstallationError, match="settings changed"):
        ClaudeDesktopRegistration(path).register(Launcher(tmp_path / "uv", tmp_path), approve)
    assert path.read_text(encoding="utf-8") == later


@pytest.mark.parametrize("source", ["{ broken JSON", "[]", '{ "mcpServers": [] }'])
def test_invalid_config_is_left_intact(tmp_path: Path, source: str) -> None:
    path = tmp_path / "claude_desktop_config.json"
    path.write_text(source, encoding="utf-8")
    with pytest.raises(InstallationError, match="Claude Desktop"):
        ClaudeDesktopRegistration(path).register(Launcher(tmp_path / "uv", tmp_path), lambda: True)
    assert path.read_text(encoding="utf-8") == source


@pytest.mark.parametrize("platform", ["win32", "darwin"])
def test_default_settings_location(tmp_path: Path, platform: str) -> None:
    app_data = tmp_path / "AppData"
    path = (
        app_data / "Claude"
        if platform == "win32"
        else tmp_path / "Library" / "Application Support" / "Claude"
    )
    with pytest.raises(InstallationError, match="open Claude Desktop once"):
        ClaudeDesktopRegistration.for_current_user(platform, {"APPDATA": str(app_data)}, tmp_path)
    path.mkdir(parents=True)
    registration = ClaudeDesktopRegistration.for_current_user(
        platform, {"APPDATA": str(app_data)}, tmp_path
    )
    registration.register(Launcher(tmp_path / "uv", tmp_path), lambda: False)
    assert (path / "claude_desktop_config.json").is_file()
