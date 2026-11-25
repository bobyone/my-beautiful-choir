# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Contract for reading authorised score content."""

from abc import ABC, abstractmethod

from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.reading.score_music import ScoreMusic


class ScoreReader(ABC):
    """Read musical content independently of its storage."""

    @abstractmethod
    async def read(self, score_format: ScoreFormat, content: bytes) -> ScoreMusic:
        """Return the musical model, or raise a score reading error."""
