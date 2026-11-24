# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Decode and validate MusicXML safely without retrieving external resources."""

import codecs
import re
from xml.parsers import expat

from my_beautiful_choir.scores.musicxml.errors import InvalidMusicXmlError
from my_beautiful_choir.scores.score_rules import MAXIMUM_SIZE

_ROOTS = {"score-partwise", "score-timewise"}
_ENCODING = re.compile(r"""^(<\?xml\s+[^?]*?\bencoding\s*=\s*)(['"])[^'"]+\2""")


def musicxml_bytes(text: str) -> bytes:
    """Normalize the encoding declaration when storing XML submitted as Unicode text."""
    try:
        return _ENCODING.sub(r'\1"UTF-8"', text.removeprefix("\ufeff"), count=1).encode("utf-8")
    except UnicodeError as error:
        raise InvalidMusicXmlError("Provide valid MusicXML text.") from error


def musicxml_text(content: bytes) -> str:
    """Validate the document and return its text, accepting UTF-8 and UTF-16."""
    if not content or len(content) > MAXIMUM_SIZE:
        raise InvalidMusicXmlError(
            "Provide a non-empty MusicXML score within the score size limit."
        )
    parser = expat.ParserCreate()
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    # MusicXML exports may declare a public DTD. Ignore it and reject entity declarations.
    parser.ExternalEntityRefHandler = lambda *_: 0
    parser.EntityDeclHandler = _reject_entity
    root: str | None = None

    def record_root(name: str, attributes: dict[str, str]) -> None:
        nonlocal root
        if root is None:
            root = name

    parser.StartElementHandler = record_root
    try:
        parser.Parse(content, True)
        encoding = (
            "utf-16"
            if content.startswith((codecs.BOM_UTF16_BE, codecs.BOM_UTF16_LE))
            else "utf-8-sig"
        )
        text = content.decode(encoding)
    except (expat.ExpatError, UnicodeError, LookupError) as error:
        raise InvalidMusicXmlError("Provide well-formed MusicXML in UTF-8 or UTF-16.") from error
    if root not in _ROOTS:
        raise InvalidMusicXmlError("Provide a partwise or timewise MusicXML score.")
    return text


def _reject_entity(*_: object) -> None:
    raise InvalidMusicXmlError("Remove custom XML entity declarations from the score.")
