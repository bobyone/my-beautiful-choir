# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Integration tests for exact timing and notation across MusicXML organisations."""

from fractions import Fraction

import pytest

from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.reading.errors import ScoreReadingError
from my_beautiful_choir.scores.reading.musicxml.musicxml_score_reader import MusicXmlScoreReader
from tests import score_samples

_PARTS = """<part-list><score-part id="P1"><part-name>Duet</part-name>
 <score-instrument id="I1"><instrument-name>Clarinet</instrument-name></score-instrument>
 </score-part></part-list>"""
_FIRST = """<attributes><divisions>12</divisions><key><fifths>2</fifths></key>
 <time><beats>3</beats><beat-type>4</beat-type></time><staves>2</staves>
 <transpose number="1"><diatonic>-1</diatonic><chromatic>-2</chromatic></transpose>
 <transpose number="2"><chromatic>0</chromatic></transpose></attributes>
 <note><pitch><step>C</step><alter>1</alter><octave>4</octave></pitch>
 <duration>8</duration><instrument id="I1"/><voice>1</voice><staff>1</staff>
 <time-modification><actual-notes>3</actual-notes><normal-notes>2</normal-notes></time-modification>
 <notations><slur number="1" type="start"/><tied type="start"/></notations>
 <lyric number="1"><syllabic>begin</syllabic><text>Hel</text></lyric>
 <lyric number="2"><text>Dox</text><extend type="start"/></lyric></note>
 <note><chord/><pitch><step>E</step><octave>4</octave></pitch><duration>8</duration>
 <voice>1</voice><staff>1</staff></note><backup><duration>8</duration></backup>
 <note print-object="no"><rest/><duration>8</duration><voice>2</voice><staff>2</staff></note>"""
_NEXT = """<print new-page="yes"/><direction><direction-type><dynamics><p/></dynamics>
 </direction-type><staff>1</staff></direction>
 <note><pitch><step>C</step><alter>1</alter><octave>4</octave></pitch><duration>12</duration>
 <voice>2</voice><staff>1</staff><notations><slur number="1" type="stop"/><tied type="stop"/>
 </notations><lyric number="1"><syllabic>end</syllabic><text>lo</text></lyric>
 <lyric number="2"><extend type="stop"/></lyric></note>"""


@pytest.mark.anyio
async def test_partwise_timewise_and_compressed_preserve_the_same_notation() -> None:
    full = (
        f'<score-partwise>{_PARTS}<part id="P1"><measure number="0" implicit="yes">'
        f'{_FIRST}</measure><measure number="1">{_NEXT}</measure></part></score-partwise>'
    ).encode()
    timewise = (
        f'<score-timewise>{_PARTS}<measure number="0" implicit="yes"><part id="P1">'
        f'{_FIRST}</part></measure><measure number="1"><part id="P1">{_NEXT}'
        "</part></measure></score-timewise>"
    ).encode()
    compressed = score_samples.zip_archive(
        {
            "META-INF/container.xml": score_samples.CONTAINER_XML.encode(),
            "score.musicxml": full,
        }
    )
    reader = MusicXmlScoreReader()
    model = await reader.read(ScoreFormat.MUSICXML, full)
    assert await reader.read(ScoreFormat.MUSICXML, timewise) == model
    assert await reader.read(ScoreFormat.COMPRESSED_MUSICXML, compressed) == model
    assert not model.unsupported
    (part,) = model.parts
    first, second = part.measures
    assert not first.unsupported
    assert not second.unsupported
    assert first.implicit
    notes = [event for event in first.events if event.kind == "note"]
    assert [note.duration for note in notes] == [Fraction(2, 3), Fraction(2, 3)]
    assert notes[0].sounding == (Fraction(59),)
    assert notes[1].offset == notes[0].offset == 0
    assert any(event.kind == "rest" and event.staff == "2" for event in first.events)
    assert {event.kind for event in second.opening} >= {"key", "time", "transpose"}
    assert any(detail.kind == "lyric" for detail in notes[0].details)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "source",
    [
        b'<score-partwise><part id="P1"/></score-partwise>',
        b'<!DOCTYPE score-partwise [<!ENTITY x "declared">]><score-partwise/>',
        b"<score-partwise>",
        b"<score-timewise>" + b"<x>" * 60 + b"</x>" * 60 + b"</score-timewise>",
    ],
)
async def test_refuses_invalid_or_excessively_nested_source(source: bytes) -> None:
    with pytest.raises(ScoreReadingError):
        await MusicXmlScoreReader().read(ScoreFormat.MUSICXML, source)
