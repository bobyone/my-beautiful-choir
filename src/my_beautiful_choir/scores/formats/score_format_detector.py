# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Recognition of the format of a score."""

from collections.abc import Sequence

from my_beautiful_choir.scores.errors import UnsupportedScoreFormatError
from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.formats.score_format_signature import ScoreFormatSignature


class ScoreFormatDetector:
    """Tries the signatures in order and gives the format of the first one that matches."""

    def __init__(self, signatures: Sequence[ScoreFormatSignature]) -> None:
        self._signatures = tuple(signatures)

    def detect(self, content: bytes) -> ScoreFormat:
        """Format of ``content``; raises ``UnsupportedScoreFormatError`` if none matches."""
        for signature in self._signatures:
            if signature.matches(content):
                return signature.format
        raise UnsupportedScoreFormatError
