# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Exceptions of the score sources."""

from pathlib import Path

from my_beautiful_choir.scores.errors import ScoresError


class ScoreSourceError(ScoresError):
    """The content of a score cannot be obtained from its source."""


class UnreadableLocalFileError(ScoreSourceError):
    """A local file does not exist, is not a regular file or cannot be read."""

    def __init__(self, path: Path, reason: str) -> None:
        super().__init__(
            f"The file {path} cannot be read: {reason}. Check the path, which must be "
            "absolute, and that the file can be read by your user."
        )
        self.path = path
        self.reason = reason
