# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests for the MusicXML text boundary."""

import pytest

from my_beautiful_choir.scores.musicxml.errors import InvalidMusicXmlError
from my_beautiful_choir.scores.musicxml.musicxml_document import musicxml_bytes, musicxml_text
from tests import score_samples


def test_round_trip_accepts_the_standard_doctype_and_unicode() -> None:
    text = score_samples.musicxml_text().replace("Soprano", "Soprano é")
    utf16 = text.replace("UTF-8", "UTF-16")
    assert musicxml_text(utf16.encode("utf-16")) == utf16
    assert musicxml_text(musicxml_bytes(utf16)) == text


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"<html/>",
        b"<score-partwise>",
        b'<!DOCTYPE score-partwise [<!ENTITY x SYSTEM "file:///no-read">]>'
        b"<score-partwise>&x;</score-partwise>",
        b'<!DOCTYPE score-partwise [<!ENTITY x "expanded">]><score-partwise>&x;</score-partwise>',
    ],
)
def test_invalid_or_entity_using_content_is_rejected(content: bytes) -> None:
    with pytest.raises(InvalidMusicXmlError):
        musicxml_text(content)
