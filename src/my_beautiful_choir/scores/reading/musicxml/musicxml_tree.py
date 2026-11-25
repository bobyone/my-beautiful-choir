# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Build a bounded tree with the existing secured XML parser."""

from __future__ import annotations

from xml.etree.ElementTree import Element, TreeBuilder
from xml.parsers.expat import ExpatError

from my_beautiful_choir.scores.musicxml.errors import InvalidMusicXmlError
from my_beautiful_choir.scores.musicxml.musicxml_document import xml_parser
from my_beautiful_choir.scores.reading.errors import ScoreReadingError
from my_beautiful_choir.scores.score_rules import MAXIMUM_SIZE

_MAX_ELEMENTS = 350_000
_MAX_DEPTH = 48
_ROOTS = {"score-partwise", "score-timewise"}


def musicxml_tree(content: bytes) -> Element[str]:
    """Parse without resolving DTDs, processing instructions or external documents."""
    if not content or len(content) > MAXIMUM_SIZE:
        raise ScoreReadingError("Choose a non-empty MusicXML score within the score size limit.")
    builder = TreeBuilder()
    depth = 0
    elements = 0

    def start(name: str, attributes: dict[str, str]) -> None:
        nonlocal depth, elements
        depth += 1
        elements += 1
        if depth > _MAX_DEPTH or elements > _MAX_ELEMENTS:
            raise ScoreReadingError("The score structure exceeds the reading limit.")
        builder.start(name, attributes)

    def end(name: str) -> None:
        nonlocal depth
        builder.end(name)
        depth -= 1

    parser = xml_parser()
    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CharacterDataHandler = builder.data
    try:
        parser.Parse(content, True)
    except (ExpatError, UnicodeError, LookupError, InvalidMusicXmlError) as error:
        raise ScoreReadingError("Choose readable MusicXML without entity declarations.") from error
    root = builder.close()
    if root.tag not in _ROOTS:
        raise ScoreReadingError("Choose a partwise or timewise MusicXML score.")
    return root
