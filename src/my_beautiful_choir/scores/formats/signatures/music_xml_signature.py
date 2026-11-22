# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Signature of the uncompressed MusicXML format."""

import codecs
import re

from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.formats.score_format_signature import ScoreFormatSignature

PROLOG_SEARCH_LENGTH = 16 * 1024

# Whitespace, XML declaration, processing instructions, comments and document
# type declaration that may come before the root element.
_PROLOG = re.compile(
    r"(?:\s+|<\?.*?\?>|<!--.*?-->|<!DOCTYPE(?:[^>\[\"']|\"[^\"]*\"|'[^']*')*(?:\[.*?\])?\s*>)*",
    re.DOTALL,
)
_ROOT = re.compile(r"<score-(?:partwise|timewise)[\s/>]")


class MusicXmlSignature(ScoreFormatSignature):
    """A MusicXML file has ``score-partwise`` or ``score-timewise`` as root element.

    Only the beginning of the file is read, as text in UTF-8, or in UTF-16 when
    it starts with a byte order mark; it is not parsed as XML, so that no
    external entity is ever resolved.
    """

    @property
    def format(self) -> ScoreFormat:
        return ScoreFormat.MUSICXML

    def matches(self, content: bytes) -> bool:
        text = _decode(content[:PROLOG_SEARCH_LENGTH])
        prolog = _PROLOG.match(text)
        start = prolog.end() if prolog else 0
        return _ROOT.match(text, start) is not None


def _decode(head: bytes) -> str:
    if head.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return head.decode("utf-16", errors="replace")
    return head.removeprefix(codecs.BOM_UTF8).decode("utf-8", errors="replace")
