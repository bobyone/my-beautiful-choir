# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Detect usable launch targets for separately installed Audiveris."""

import asyncio
import os
import shutil
import sys
from collections.abc import Callable, Iterable, Mapping
from functools import partial
from pathlib import Path

from my_beautiful_choir.scores.recognition.audiveris.launch import AudiverisLaunch
from my_beautiful_choir.scores.recognition.errors import (
    EngineNotFoundError,
    EngineUnavailableError,
)

_FLATPAK_ID = "org.audiveris.audiveris"


class AudiverisInstallation:
    """Find Audiveris using the system registry, applications, packages, or PATH."""

    def __init__(
        self, override: Path | None, platform: str, environment: Mapping[str, str], home: Path
    ) -> None:
        self._override = override
        self._platform = platform
        self._environment = environment
        self._home = home

    async def discover(self) -> AudiverisLaunch:
        """Return a launch description for a discovered installation."""
        return await asyncio.to_thread(self._discover)

    def _discover(self) -> AudiverisLaunch:
        if self._override is not None:
            candidate = self._override.expanduser()
            if not candidate.is_absolute() or not _executable(candidate):
                raise EngineUnavailableError()
            return AudiverisLaunch(candidate)

        path = self._environment.get("PATH", os.defpath)
        candidates = list(self._native_paths())
        for name in ("audiveris", "Audiveris"):
            if found := shutil.which(name, path=path):
                candidates.append(Path(found))
        for candidate in candidates:
            if _executable(candidate):
                return AudiverisLaunch(candidate.resolve())
        if self._platform.startswith("linux"):
            flatpak = shutil.which("flatpak", path=path)
            if flatpak and Path(flatpak).is_absolute() and _flatpak_installed(Path(flatpak)):
                return AudiverisLaunch(Path(flatpak), flatpak_app_id=_FLATPAK_ID)
        if any(candidate.exists() for candidate in candidates):
            raise EngineUnavailableError()
        raise EngineNotFoundError()

    def _native_paths(self) -> Iterable[Path]:
        if self._platform == "win32":
            yield from _windows_registry()
            for variable in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)", "LOCALAPPDATA"):
                if directory := self._environment.get(variable):
                    root = Path(directory)
                    yield root / "Audiveris" / "Audiveris.exe"
                    yield root / "Programs" / "Audiveris" / "Audiveris.exe"
            yield self._home / "scoop" / "apps" / "audiveris" / "current" / "Audiveris.exe"
            for variable in ("SCOOP", "SCOOP_GLOBAL"):
                if directory := self._environment.get(variable):
                    yield Path(directory) / "apps" / "audiveris" / "current" / "Audiveris.exe"
        elif self._platform == "darwin":
            folders = (Path(self._home.anchor) / "Applications", self._home / "Applications")
            for folder in folders:
                executables = folder / "Audiveris.app" / "Contents" / "MacOS"
                yield executables / "Audiveris"
                yield executables / "audiveris"
            yield from _mac_indexed_paths(folders)
        elif self._platform.startswith("linux"):
            system_root = Path(self._home.anchor)
            yield system_root / "opt" / "audiveris" / "bin" / "Audiveris"
            yield self._home / ".local" / "bin" / "audiveris"


def _executable(candidate: Path) -> bool:
    if not candidate.is_absolute() or not candidate.is_file():
        return False
    # A Windows batch file can invoke cmd implicitly in subprocess.
    return (
        candidate.suffix.casefold() == ".exe"
        if sys.platform == "win32"
        else os.access(candidate, os.X_OK)
    )


def _windows_registry() -> Iterable[Path]:
    if sys.platform != "win32":
        return
    import winreg

    uninstall = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    lookup = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Audiveris.exe"
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            access = winreg.KEY_READ | view
            try:
                with winreg.OpenKey(hive, lookup, 0, access) as key:
                    value, _ = winreg.QueryValueEx(key, "")
                    if isinstance(value, str):
                        yield Path(os.path.expandvars(value.strip('"')))
            except OSError:
                pass
            try:
                with winreg.OpenKey(hive, uninstall, 0, access) as root:
                    for index in range(winreg.QueryInfoKey(root)[0]):
                        try:
                            with winreg.OpenKey(root, winreg.EnumKey(root, index)) as key:
                                name, _ = winreg.QueryValueEx(key, "DisplayName")
                                if isinstance(name, str) and name.casefold().startswith(
                                    "audiveris"
                                ):
                                    yield from _windows_install_paths(
                                        partial(winreg.QueryValueEx, key)
                                    )
                        except OSError:
                            continue
            except OSError:
                continue


def _windows_install_paths(
    read_value: Callable[[str], tuple[object, int]],
) -> Iterable[Path]:
    for field in ("InstallLocation", "DisplayIcon"):
        try:
            value, _ = read_value(field)
        except OSError:
            continue
        if isinstance(value, str) and value:
            raw = os.path.expandvars(value.strip())
            if field == "InstallLocation":
                yield Path(raw.strip('"')) / "Audiveris.exe"
            else:
                icon = Path(raw.rsplit(",", 1)[0].strip('"'))
                if icon.name.casefold() == "audiveris.exe":
                    yield icon


def _mac_indexed_paths(folders: tuple[Path, ...]) -> Iterable[Path]:
    import subprocess

    mdfind = shutil.which("mdfind")
    if mdfind is None or not Path(mdfind).is_absolute():
        return
    scopes = [argument for folder in folders for argument in ("-onlyin", str(folder))]
    try:
        result = subprocess.run(  # noqa: S603
            [mdfind, *scopes, "kMDItemFSName == 'Audiveris.app'"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=3,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return
    for line in result.stdout.decode("utf-8", errors="replace").splitlines():
        bundle = Path(line)
        if bundle.name == "Audiveris.app" and any(bundle.is_relative_to(root) for root in folders):
            yield bundle / "Contents" / "MacOS" / "Audiveris"


def _flatpak_installed(executable: Path) -> bool:
    import subprocess

    try:
        return (
            subprocess.run(  # noqa: S603
                [str(executable), "info", _FLATPAK_ID],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
                check=False,
            ).returncode
            == 0
        )
    except (OSError, subprocess.SubprocessError):
        return False
