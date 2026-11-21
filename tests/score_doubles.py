# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Doubles of the file storage, the score sources and the score opener."""

from my_beautiful_choir.scores.errors import InvalidScoreSizeError
from my_beautiful_choir.scores.opening.score_opener import ScoreOpener
from my_beautiful_choir.scores.score import Score
from my_beautiful_choir.scores.score_origin import ScoreOrigin
from my_beautiful_choir.scores.sources.score_content import ScoreContent
from my_beautiful_choir.scores.sources.score_source import ScoreSource
from my_beautiful_choir.storage.errors import StorageError
from my_beautiful_choir.storage.file_storage import FileStorage, check_storage_key


class InMemoryFileStorage(FileStorage):
    """Stored contents kept in a dictionary; ``failing`` makes ``store`` fail."""

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}
        self.failing = False

    async def store(self, key: str, content: bytes) -> None:
        if self.failing:
            raise StorageError(key, "disk full")
        self.files[check_storage_key(key)] = content

    async def read(self, key: str) -> bytes:
        if check_storage_key(key) not in self.files:
            raise StorageError(key, "no such file")
        return self.files[key]

    async def delete(self, key: str) -> None:
        self.files.pop(check_storage_key(key), None)

    async def exists(self, key: str) -> bool:
        return check_storage_key(key) in self.files


class StubScoreSource(ScoreSource):
    """Gives a fixed content, honouring the limit; records the limit it was given."""

    def __init__(
        self,
        content: bytes,
        original_name: str = "Ave Maria.pdf",
        origin: ScoreOrigin = ScoreOrigin.FILE_PICKER,
        link: str | None = None,
    ) -> None:
        self._content = content
        self._original_name = original_name
        self._origin = origin
        self._link = link
        self.limits: list[int] = []

    @property
    def origin(self) -> ScoreOrigin:
        return self._origin

    @property
    def link(self) -> str | None:
        return self._link

    async def fetch(self, limit: int) -> ScoreContent:
        self.limits.append(limit)
        if len(self._content) > limit:
            raise InvalidScoreSizeError(limit)
        return ScoreContent(self._original_name, self._content)


class SpyScoreOpener(ScoreOpener):
    """Records the scores it is asked to open; ``error`` makes it fail."""

    def __init__(self, error: Exception | None = None) -> None:
        self.opened: list[tuple[Score, bytes]] = []
        self.error = error

    async def open(self, score: Score, content: bytes) -> None:
        if self.error is not None:
            raise self.error
        self.opened.append((score, content))
