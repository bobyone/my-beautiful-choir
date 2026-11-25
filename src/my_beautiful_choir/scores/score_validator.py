# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Validation contract for draft scores."""

from abc import ABC, abstractmethod

from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.validation_report import ValidationReport


class ScoreValidator(ABC):
    """Validate draft content independently of its storage."""

    @abstractmethod
    async def validate(self, score_format: ScoreFormat, content: bytes) -> ValidationReport:
        """Return the errors that prevent finalisation, if any."""
