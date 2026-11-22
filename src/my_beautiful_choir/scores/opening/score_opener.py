# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Score opener abstraction."""

from abc import ABC, abstractmethod

from my_beautiful_choir.scores.score import Score


class ScoreOpener(ABC):
    """Shows a score to the user, in the application that opens its format."""

    @abstractmethod
    async def open(self, score: Score, content: bytes) -> None:
        """Open the score, whose content is given.

        Raises:
            ScoreOpenError: if no application can open it.
        """
