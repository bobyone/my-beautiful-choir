# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""MusicXML adapter to the shared musical model."""

from __future__ import annotations

import asyncio
from xml.etree.ElementTree import Element

from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.musicxml.compressed_musicxml_document import (
    compressed_musicxml_bytes,
)
from my_beautiful_choir.scores.musicxml.errors import InvalidMusicXmlError
from my_beautiful_choir.scores.reading.errors import ScoreReadingError
from my_beautiful_choir.scores.reading.musicxml.details import GRAPHICAL_ELEMENTS, notation
from my_beautiful_choir.scores.reading.musicxml.measure_reader import MeasureReader
from my_beautiful_choir.scores.reading.musicxml.musicxml_tree import musicxml_tree
from my_beautiful_choir.scores.reading.notation import Notation
from my_beautiful_choir.scores.reading.part import Part
from my_beautiful_choir.scores.reading.score_music import ScoreMusic
from my_beautiful_choir.scores.reading.score_reader import ScoreReader


class MusicXmlScoreReader(ScoreReader):
    """Normalise plain and compressed MusicXML in both document organisations."""

    async def read(self, score_format: ScoreFormat, content: bytes) -> ScoreMusic:
        return await asyncio.to_thread(_read, score_format, content)


def _read(score_format: ScoreFormat, content: bytes) -> ScoreMusic:
    try:
        if score_format is ScoreFormat.COMPRESSED_MUSICXML:
            content = compressed_musicxml_bytes(content)
        elif score_format is not ScoreFormat.MUSICXML:
            raise ScoreReadingError("Choose a MusicXML or compressed MusicXML score.")
    except InvalidMusicXmlError as error:
        raise ScoreReadingError(str(error)) from error

    root = musicxml_tree(content)
    declaration = _indexed(root.findall("part-list/score-part"))
    if not declaration:
        raise ScoreReadingError("The score contains no declared parts.")
    measures = _measures(root, declaration)
    unsupported = {
        element.tag
        for element in root
        if element.tag not in GRAPHICAL_ELEMENTS | {"part", "measure", "part-list", "defaults"}
    }
    parts = []
    for position, (part_id, entry) in enumerate(declaration.items(), 1):
        instruments, instrument_ids = _instruments(entry, unsupported)
        reader = MeasureReader(
            instrument_ids, concert=root.find("defaults/concert-score") is not None
        )
        parts.append(
            Part(
                position,
                entry.findtext("part-name", ""),
                instruments,
                tuple(
                    reader.read(index, framing, data)
                    for index, (framing, data) in enumerate(measures[part_id], 1)
                ),
            )
        )
    return ScoreMusic(tuple(parts), tuple(sorted(unsupported)))


def _indexed(elements: list[Element[str]]) -> dict[str, Element[str]]:
    result: dict[str, Element[str]] = {}
    for element in elements:
        part_id = element.get("id", "")
        if not part_id or part_id in result:
            raise ScoreReadingError("The score contains missing or repeated part identifiers.")
        result[part_id] = element
    return result


def _measures(
    root: Element[str], declarations: dict[str, Element[str]]
) -> dict[str, list[tuple[Element[str], Element[str]]]]:
    if root.tag == "score-partwise":
        bodies = _indexed(root.findall("part"))
        if bodies.keys() != declarations.keys():
            raise ScoreReadingError("The declared parts do not match the score's content.")
        return {
            part_id: [(measure, measure) for measure in part.findall("measure")]
            for part_id, part in bodies.items()
        }
    output: dict[str, list[tuple[Element[str], Element[str]]]] = {
        part_id: [] for part_id in declarations
    }
    for measure in root.findall("measure"):
        for part_id, part in _indexed(measure.findall("part")).items():
            if part_id not in output:
                raise ScoreReadingError("A measure refers to a part that is not declared.")
            output[part_id].append((measure, part))
    return output


def _instruments(
    part: Element[str], unsupported: set[str]
) -> tuple[tuple[Notation, ...], dict[str, int]]:
    instruments = []
    lookup = {}
    for element in part.findall("score-instrument"):
        instrument_id = element.get("id")
        if not instrument_id or instrument_id in lookup:
            raise ScoreReadingError(
                "The score contains missing or repeated instrument identifiers."
            )
        if instrument := notation(element, unsupported):
            instruments.append(instrument)
            lookup[instrument_id] = len(instruments)
    return tuple(instruments), lookup
