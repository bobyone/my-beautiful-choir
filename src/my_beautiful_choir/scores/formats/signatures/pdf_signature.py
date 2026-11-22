# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Signature of the PDF format."""

from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.formats.score_format_signature import ScoreFormatSignature

HEADER = b"%PDF-"
HEADER_SEARCH_LENGTH = 1024


class PdfSignature(ScoreFormatSignature):
    """A PDF file has the ``%PDF-`` header within its first 1024 bytes."""

    @property
    def format(self) -> ScoreFormat:
        return ScoreFormat.PDF

    def matches(self, content: bytes) -> bool:
        return HEADER in content[:HEADER_SEARCH_LENGTH]
