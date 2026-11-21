# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the MusicXML signature."""

import codecs

import pytest

from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.formats.signatures.music_xml_signature import MusicXmlSignature
from tests import score_samples


@pytest.mark.parametrize(
    "content",
    [
        score_samples.musicxml(),
        score_samples.musicxml_text("score-timewise").encode("utf-8"),
        b'<score-partwise version="4.0"/>',
        b"\n  <score-partwise>",
        codecs.BOM_UTF8 + score_samples.musicxml(),
        codecs.BOM_UTF16_LE + score_samples.musicxml_text().encode("utf-16-le"),
        codecs.BOM_UTF16_BE + score_samples.musicxml_text().encode("utf-16-be"),
        b'<?xml version="1.0"?>\n<!-- exported by an editor > 1.0 -->\n'
        b'<?editor setting="a"?>\n<score-partwise>',
        b'<!DOCTYPE score-partwise [ <!ENTITY a "b"> ]>\n<score-partwise>',
    ],
)
def test_recognizes_musicxml(content: bytes) -> None:
    signature = MusicXmlSignature()
    assert signature.format is ScoreFormat.MUSICXML
    assert signature.matches(content)


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"Hello",
        b'<?xml version="1.0"?>\n<opus version="4.0"/>',
        b'<?xml version="1.0"?>\n<html><score-partwise></score-partwise></html>',
        b"<!-- <score-partwise> -->\n<html/>",
        b"<score-partwisex>",
        b"<score-partwise",
        b"text before <score-partwise>",
        score_samples.musicxml_text().encode("utf-16-le"),
        b" " * (16 * 1024) + b"<score-partwise>",
        score_samples.pdf(),
        score_samples.compressed_musicxml(),
    ],
)
def test_refuses_other_content(content: bytes) -> None:
    assert not MusicXmlSignature().matches(content)
