# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Opening a temporary copy of a score with the default application of the system."""

import asyncio
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

from my_beautiful_choir.scores.errors import ScoreOpenError
from my_beautiful_choir.scores.opening.score_opener import ScoreOpener
from my_beautiful_choir.scores.score import Score

TEMPORARY_DIRECTORY_NAME = "my-beautiful-choir"
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


class SystemScoreOpener(ScoreOpener):
    """Writes a temporary copy of the score, then opens it with the default application.

    The stored score never changes: an edit made in the application (in
    MuseScore, for instance) only changes the copy. Each score has its own
    subdirectory, whose copy is replaced at each opening; the copies are left
    for the system to clean its temporary directory. The file name comes from
    the label, reduced to letters, digits, spaces, ``-`` and ``_``.
    """

    def __init__(self, directory: Path, launch: Launcher) -> None:
        self._directory = directory
        self._launch = launch

    @classmethod
    def in_temporary_directory(cls) -> "SystemScoreOpener":
        """Opener of personal mode, in the temporary directory of the system."""
        return cls(Path(tempfile.gettempdir()) / TEMPORARY_DIRECTORY_NAME, system_launcher())

    @property
    def directory(self) -> Path:
        """Directory of the temporary copies."""
        return self._directory

    async def open(self, score: Score, content: bytes) -> None:
        await asyncio.to_thread(self._open, score, content)

    def _open(self, score: Score, content: bytes) -> None:
        name = _UNSAFE_CHARACTERS.sub("_", score.label)[:FILE_NAME_LENGTH].strip() or "score"
        path = self._directory / str(score.id) / f"{name}{score.format.extension}"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
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
