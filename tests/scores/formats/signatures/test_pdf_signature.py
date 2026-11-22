# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the PDF signature."""

import pytest

from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.formats.signatures.pdf_signature import PdfSignature
from tests import score_samples


def test_recognizes_a_pdf() -> None:
    signature = PdfSignature()
    assert signature.format is ScoreFormat.PDF
    assert signature.matches(score_samples.pdf())


def test_the_header_may_follow_some_bytes() -> None:
    assert PdfSignature().matches(b"\x00" * 1000 + score_samples.pdf())


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"%PDF",
        b"\x00" * 1024 + b"%PDF-1.7",
        b"Hello",
        score_samples.musicxml(),
        score_samples.musescore(),
    ],
)
def test_refuses_other_content(content: bytes) -> None:
    assert not PdfSignature().matches(content)
