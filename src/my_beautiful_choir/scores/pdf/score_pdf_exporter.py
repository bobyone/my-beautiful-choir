# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Contract for rendering an editable score to PDF."""

from abc import ABC, abstractmethod

from my_beautiful_choir.scores.formats.score_format import ScoreFormat


class ScorePdfExporter(ABC):
    """Render a score copy without changing the stored notation."""

    @abstractmethod
    async def export(self, score_format: ScoreFormat, content: bytes) -> bytes:
        """Return a PDF or raise a score PDF export error."""
