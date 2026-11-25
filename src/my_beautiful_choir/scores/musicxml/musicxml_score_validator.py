# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Structural validator for the editable score formats."""

import asyncio

from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.musicxml.compressed_musicxml_document import (
    compressed_musicxml_bytes,
)
from my_beautiful_choir.scores.musicxml.errors import InvalidMusicXmlError
from my_beautiful_choir.scores.musicxml.musicxml_document import musicxml_text
from my_beautiful_choir.scores.score_validator import ScoreValidator
from my_beautiful_choir.scores.validation_report import ValidationReport


class MusicXmlScoreValidator(ScoreValidator):
    """Check the format, container and well-formedness of a MusicXML draft."""

    async def validate(self, score_format: ScoreFormat, content: bytes) -> ValidationReport:
        return await asyncio.to_thread(_validate, score_format, content)


def _validate(score_format: ScoreFormat, content: bytes) -> ValidationReport:
    try:
        if score_format is ScoreFormat.COMPRESSED_MUSICXML:
            content = compressed_musicxml_bytes(content)
        elif score_format is not ScoreFormat.MUSICXML:
            return ValidationReport(("Choose a MusicXML draft to finalise.",))
        musicxml_text(content)
    except InvalidMusicXmlError as error:
        return ValidationReport((str(error),))
    return ValidationReport()
