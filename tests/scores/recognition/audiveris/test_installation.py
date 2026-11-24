# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Exercise local Audiveris installation discovery on all supported platforms."""

import shutil
import sys
from collections.abc import Iterator
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from my_beautiful_choir.scores.recognition.audiveris import installation
from my_beautiful_choir.scores.recognition.audiveris.installation import AudiverisInstallation
from my_beautiful_choir.scores.recognition.errors import EngineNotFoundError, EngineUnavailableError


@pytest.mark.anyio
async def test_missing_engine_and_invalid_override(tmp_path: Path) -> None:
    with pytest.raises(EngineNotFoundError, match=r"https://audiveris\.github\.io"):
        await AudiverisInstallation(None, "unknown", {"PATH": str(tmp_path)}, tmp_path).command()
    with pytest.raises(EngineUnavailableError, match=r"https://audiveris\.github\.io"):
        await AudiverisInstallation(tmp_path / "missing.exe", "win32", {}, tmp_path).command()


@pytest.mark.anyio
async def test_windows_registry_tracks_a_custom_location(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    executable = tmp_path / "Custom Audiveris" / "Audiveris.exe"
    executable.parent.mkdir()
    executable.touch()

    def open_key(hive: int | str, path: str, *unused: int) -> nullcontext[str]:
        return nullcontext(path)

    def query_value(key: str, value: str) -> tuple[str, int]:
        if value == "DisplayName" and key == "audiveris":
            return "Audiveris 5", 1
        if value == "DisplayIcon" and key == "audiveris":
            return f'"{executable}",0', 1
        raise FileNotFoundError(value)

    registry = SimpleNamespace(
        HKEY_CURRENT_USER=1,
        HKEY_LOCAL_MACHINE=2,
        KEY_WOW64_64KEY=4,
        KEY_WOW64_32KEY=8,
        KEY_READ=16,
        OpenKey=open_key,
        QueryValueEx=query_value,
        QueryInfoKey=lambda _: (1, 0, 0),
        EnumKey=lambda *_: "audiveris",
    )
    monkeypatch.setitem(sys.modules, "winreg", registry)
    assert executable in list(installation._windows_registry())
    monkeypatch.setattr(installation, "_executable", Path.is_file)
    command = await AudiverisInstallation(None, "win32", {}, tmp_path).command()
    assert command == (str(executable.resolve()),)


@pytest.mark.anyio
async def test_mac_native_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    executable = tmp_path / "Audiveris.app" / "Contents" / "MacOS" / "Audiveris"
    executable.parent.mkdir(parents=True)
    executable.touch()

    def indexed(folders: tuple[Path, ...]) -> Iterator[Path]:
        yield executable

    monkeypatch.setattr(installation, "_mac_indexed_paths", indexed)
    monkeypatch.setattr(installation, "_executable", Path.is_file)
    command = await AudiverisInstallation(None, "darwin", {}, tmp_path).command()
    assert command == (str(executable.resolve()),)


@pytest.mark.anyio
async def test_linux_flatpak(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    executable = tmp_path / "flatpak"
    monkeypatch.setattr(
        shutil,
        "which",
        lambda name, **options: str(executable) if name == "flatpak" else None,
    )
    monkeypatch.setattr(installation, "_flatpak_installed", lambda path: path == executable)
    command = await AudiverisInstallation(None, "linux", {}, tmp_path).command()
    assert command == (str(executable), "run", "org.audiveris.audiveris")
