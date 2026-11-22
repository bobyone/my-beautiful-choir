# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the score format detector."""

import pytest

from my_beautiful_choir.errors import DomainError
from my_beautiful_choir.scores.errors import UnsupportedScoreFormatError
from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.formats.score_format_detector import ScoreFormatDetector
from my_beautiful_choir.scores.formats.score_format_signature import ScoreFormatSignature


class _StubSignature(ScoreFormatSignature):
    def __init__(self, score_format: ScoreFormat, matching: bool) -> None:
        self._format = score_format
        self._matching = matching
        self.calls = 0

    @property
    def format(self) -> ScoreFormat:
        return self._format

    def matches(self, content: bytes) -> bool:
        self.calls += 1
        return self._matching


def test_gives_the_format_of_the_first_matching_signature() -> None:
    first = _StubSignature(ScoreFormat.PDF, matching=False)
    second = _StubSignature(ScoreFormat.MUSESCORE, matching=True)
    third = _StubSignature(ScoreFormat.COMPRESSED_MUSICXML, matching=True)
    detector = ScoreFormatDetector([first, second, third])
    assert detector.detect(b"content") is ScoreFormat.MUSESCORE
    assert (first.calls, second.calls, third.calls) == (1, 1, 0)


def test_unknown_content_lists_the_accepted_formats() -> None:
    detector = ScoreFormatDetector([_StubSignature(ScoreFormat.PDF, matching=False)])
    with pytest.raises(UnsupportedScoreFormatError) as raised:
        detector.detect(b"content")
    assert isinstance(raised.value, DomainError)
    assert str(raised.value) == (
        "The file is not a score in a supported format. Accepted formats: PDF (.pdf), "
        "MusicXML (.musicxml), compressed MusicXML (.mxl), MuseScore (.mscz)."
    )
