# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Score read from a file of the user's computer, named by its path."""

import asyncio
from pathlib import Path

from my_beautiful_choir.scores.errors import InvalidScoreSizeError
from my_beautiful_choir.scores.score_origin import ScoreOrigin
from my_beautiful_choir.scores.sources.errors import UnreadableLocalFileError
from my_beautiful_choir.scores.sources.score_content import ScoreContent
from my_beautiful_choir.scores.sources.score_source import ScoreSource


class LocalFileScoreSource(ScoreSource):
    """Reads a regular file given by an absolute path; ``~`` is the user's home directory.

    The path may come from the model: whatever it designates, only a regular
    file is read (never a device or a pipe), never more than the limit, and
    the score service then refuses any content that is not a score.
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def origin(self) -> ScoreOrigin:
        return ScoreOrigin.LOCAL_FILE

    async def fetch(self, limit: int) -> ScoreContent:
        return await asyncio.to_thread(self._read, limit)

    def _read(self, limit: int) -> ScoreContent:
        path = self._resolve()
        try:
            if not path.is_file():
                raise UnreadableLocalFileError(path, "it does not exist or is not a file")
            with path.open("rb") as file:
                content = file.read(limit + 1)
        except OSError as error:
            raise UnreadableLocalFileError(path, error.strerror or type(error).__name__) from error
        if len(content) > limit:
            raise InvalidScoreSizeError(limit)
        return ScoreContent(original_name=path.name, content=content)

    def _resolve(self) -> Path:
        try:
            path = self._path.expanduser()
        except RuntimeError as error:
            raise UnreadableLocalFileError(self._path, "the home directory is unknown") from error
        if not path.is_absolute():
            raise UnreadableLocalFileError(path, "the path is not absolute")
        return path
