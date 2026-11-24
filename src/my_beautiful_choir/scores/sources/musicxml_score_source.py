# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""A score provided directly as MusicXML by the model or recognition engine."""

from my_beautiful_choir.scores.errors import InvalidScoreSizeError
from my_beautiful_choir.scores.score_origin import ScoreOrigin
from my_beautiful_choir.scores.sources.score_content import ScoreContent
from my_beautiful_choir.scores.sources.score_source import ScoreSource


class MusicXmlScoreSource(ScoreSource):
    """Supplies validated, uncompressed MusicXML with a download name."""

    def __init__(self, content: bytes, name: str, origin: ScoreOrigin) -> None:
        self._content = content
        self._name = name
        self._origin = origin

    @property
    def origin(self) -> ScoreOrigin:
        return self._origin

    async def fetch(self, limit: int) -> ScoreContent:
        """Return the score within the requested size limit."""
        if len(self._content) > limit:
            raise InvalidScoreSizeError(limit)
        return ScoreContent(self._name, self._content)
