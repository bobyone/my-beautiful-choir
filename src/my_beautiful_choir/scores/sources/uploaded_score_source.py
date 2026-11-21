# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Score sent by a view, chosen by the user with the file picker."""

from my_beautiful_choir.scores.errors import InvalidScoreSizeError
from my_beautiful_choir.scores.sources.score_content import ScoreContent
from my_beautiful_choir.scores.sources.score_source import ScoreSource


class UploadedScoreSource(ScoreSource):
    """Content already received from a view, with the name of the file the user chose."""

    def __init__(self, file_name: str, content: bytes) -> None:
        self._file_name = file_name
        self._content = content

    async def fetch(self, limit: int) -> ScoreContent:
        if len(self._content) > limit:
            raise InvalidScoreSizeError(limit)
        return ScoreContent(original_name=self._file_name, content=self._content)
