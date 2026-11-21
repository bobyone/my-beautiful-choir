# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Score source abstraction."""

from abc import ABC, abstractmethod

from my_beautiful_choir.scores.sources.score_content import ScoreContent


class ScoreSource(ABC):
    """Gives the content of a score being added: sent by a view, read from a file, downloaded."""

    @abstractmethod
    async def fetch(self, limit: int) -> ScoreContent:
        """Content of the score, of at most ``limit`` bytes.

        Stops as soon as the content exceeds ``limit`` bytes and raises
        ``InvalidScoreSizeError``; raises a ``ScoreSourceError`` when the
        content cannot be obtained. An empty content is returned as is.
        """
