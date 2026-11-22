# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""The installer verifies the server before modifying client settings."""

from collections.abc import Callable
from pathlib import Path

import pytest
from scripts.installer.client import ClientRegistration
from scripts.installer.errors import InstallationError
from scripts.installer.launcher import Launcher

from scripts.installer import installer


class RecordingClient(ClientRegistration):
    """Saves the launcher received from the installer."""

    def __init__(self) -> None:
        self.launcher: Launcher | None = None

    def register(self, launcher: Launcher, confirm_replace: Callable[[], bool]) -> None:
        self.launcher = launcher


@pytest.mark.parametrize("probe_passes", [True, False])
def test_verification_precedes_registration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, probe_passes: bool
) -> None:
    for name in ("uv.lock", "noxfile.py"):
        (tmp_path / name).write_text("", encoding="utf-8")
    commands: list[list[str]] = []
    client = RecordingClient()

    def run(command: list[str], **options: object) -> None:
        assert options["cwd"] == tmp_path
        commands.append(command)
        assert client.launcher is None
        if "scripts.installer.probe" in command and not probe_passes:
            raise InstallationError("Failed probe")

    monkeypatch.setattr(installer, "run_command", run)
    monkeypatch.setattr(installer, "executable", lambda name, path: tmp_path / name)
    if probe_passes:
        installer.install(tmp_path, client, lambda: False, {})
        assert client.launcher == Launcher(tmp_path / "uv", tmp_path)
    else:
        with pytest.raises(InstallationError, match="Failed probe"):
            installer.install(tmp_path, client, lambda: False, {})
        assert client.launcher is None
    assert len(commands) == 3
    assert commands[0][1:] == ["sync", "--frozen"]
    assert commands[1][-3:] == ["nox", "-s", "ui"]
    assert commands[2][-9:] == list(Launcher(tmp_path / "uv", tmp_path).command)
