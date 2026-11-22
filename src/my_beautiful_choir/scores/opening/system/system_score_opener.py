# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Opening a temporary copy of a score with the default application of the system."""

import asyncio
import errno
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from threading import Lock

from my_beautiful_choir.scores.errors import ScoreOpenError
from my_beautiful_choir.scores.opening.score_opener import ScoreOpener
from my_beautiful_choir.scores.score import Score

TEMPORARY_DIRECTORY_PREFIX = "my-beautiful-choir-"
LAUNCH_TIMEOUT_SECONDS = 30.0
FILE_NAME_LENGTH = 100

_UNSAFE_CHARACTERS = re.compile(r"[^\w\- ]+")

type Launcher = Callable[[Path], None]
"""Opens a file with its default application; raises ``OSError`` or
``subprocess.SubprocessError`` when it cannot."""


def system_launcher(platform: str = sys.platform) -> Launcher:
    """Launcher of the platform: ``os.startfile`` on Windows, ``open`` on macOS,
    ``xdg-open`` elsewhere."""
    if platform == "win32":
        return _start_file
    command = "open" if platform == "darwin" else "xdg-open"

    def launch(path: Path) -> None:
        subprocess.run(  # noqa: S603 - fixed command, the path is ours
            [command, str(path)],
            check=True,
            # The standard input of personal mode is the MCP channel: never shared.
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=LAUNCH_TIMEOUT_SECONDS,
        )

    return launch


def _start_file(path: Path) -> None:
    os.startfile(path)  # type: ignore[attr-defined,unused-ignore]  # noqa: S606 - Windows only


def _write_private_copy(path: Path, content: bytes) -> None:
    """Replace the destination with a privately created, fully written file."""
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as file:
            temporary = Path(file.name)
            file.write(content)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class SystemScoreOpener(ScoreOpener):
    """Writes a temporary copy of the score, then opens it with the default application.

    The stored score never changes: an edit made in the application (in
    MuseScore, for instance) only changes the copy. Each score has its own
    subdirectory, whose copy is replaced at each opening; the copies are left
    for the system to clean its temporary directory. Personal mode creates
    a private temporary directory on first use. The file name comes from
    the label, reduced to letters, digits, spaces, ``-`` and ``_``.
    """

    def __init__(self, directory: Path | None, launch: Launcher) -> None:
        self._directory = directory
        self._directory_lock = Lock()
        self._launch = launch

    @classmethod
    def in_temporary_directory(cls) -> "SystemScoreOpener":
        """Opener of personal mode, in the temporary directory of the system."""
        return cls(None, system_launcher())

    @property
    def directory(self) -> Path:
        """Directory of the temporary copies."""
        with self._directory_lock:
            if self._directory is None:
                self._directory = Path(tempfile.mkdtemp(prefix=TEMPORARY_DIRECTORY_PREFIX))
            return self._directory

    async def open(self, score: Score, content: bytes) -> None:
        await asyncio.to_thread(self._open, score, content)

    def _open(self, score: Score, content: bytes) -> None:
        name = _UNSAFE_CHARACTERS.sub("_", score.label)[:FILE_NAME_LENGTH].strip() or "score"
        try:
            directory = self.directory / str(score.id)
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            if directory.is_symlink() or directory.is_junction():
                raise NotADirectoryError(errno.ENOTDIR, "the temporary score directory is a link")
            if os.name == "posix":
                directory.chmod(0o700)
            path = directory / f"{name}{score.format.extension}"
            _write_private_copy(path, content)
        except OSError as error:
            raise ScoreOpenError(
                score.format, f"its temporary copy cannot be written ({error.strerror})"
            ) from error
        try:
            self._launch(path)
        except (OSError, subprocess.SubprocessError) as error:
            raise ScoreOpenError(
                score.format, "no application of your computer opened it"
            ) from error
