# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Compare content and test ambiguous label matching independently of MCP."""

from dataclasses import replace

import pytest

from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.reading.errors import ScoreComparisonError, ScoreSelectionError
from my_beautiful_choir.scores.reading.match import Match
from my_beautiful_choir.scores.reading.measure_range import read_range
from my_beautiful_choir.scores.reading.musicxml.musicxml_score_reader import MusicXmlScoreReader
from my_beautiful_choir.scores.reading.part_match import PartMatch
from my_beautiful_choir.scores.reading.score_comparison import compare_music

_SCORE = """<score-partwise><part-list><score-part id="P1"><part-name>Voice</part-name>
 </score-part></part-list><part id="P1"><measure number="9">
 <attributes><divisions>4</divisions><time><beats>4</beats><beat-type>4</beat-type></time></attributes>
 <direction placement="above"><direction-type><dynamics><p/></dynamics></direction-type></direction>
 <note default-x="25"><pitch><step>C</step><alter>1</alter><octave>4</octave></pitch>
 <duration>4</duration><lyric><text>original</text></lyric></note>
 </measure></part></score-partwise>"""


@pytest.mark.anyio
async def test_compares_musical_categories_and_ignores_graphics_and_divisions() -> None:
    reader = MusicXmlScoreReader()
    plain = await reader.read(ScoreFormat.MUSICXML, _SCORE.encode())
    rearranged = (
        _SCORE.replace('placement="above"', 'placement="below"')
        .replace('default-x="25"', 'default-x="33"')
        .replace("<duration>4", "<duration>8")
        .replace("<divisions>4", "<divisions>8")
        .replace('<measure number="9">', '<measure number="9"><print new-page="yes"/>')
    )
    unchanged = await reader.read(ScoreFormat.MUSICXML, rearranged.encode())
    assert list(compare_music(plain, unchanged, ())) == []
    edited = (
        rearranged.replace("<step>C</step><alter>1", "<step>D</step><alter>-1")
        .replace("original", "changed")
        .replace("<p/>", "<ff/>")
    )
    changed = await reader.read(ScoreFormat.MUSICXML, edited.encode())
    (entry,) = compare_music(plain, changed, ())
    assert entry["changes"] == ["dynamics", "lyrics", "written_spelling"]


@pytest.mark.anyio
async def test_reports_repeat_changes_and_retains_final_barline() -> None:
    source = _SCORE.replace(
        "</measure></part>",
        '<barline location="right"><ending number="1" type="stop"/>'
        '<repeat direction="backward" times="2"/></barline></measure>'
        '<measure number="10"><barline location="right">'
        "<bar-style>light-heavy</bar-style></barline></measure></part>",
    )
    reader = MusicXmlScoreReader()
    before = await reader.read(ScoreFormat.MUSICXML, source.encode())
    repeat, final = before.parts[0].measures
    assert not repeat.unsupported
    assert not final.unsupported
    (repeat_barline,) = (event for event in repeat.events if event.kind == "barline")
    assert [item.kind for item in repeat_barline.details[0].details] == ["ending", "repeat"]
    (final_barline,) = final.events
    assert final_barline.details[0].details[0].value == "light-heavy"
    assert list(compare_music(before, before, ())) == []

    after = await reader.read(
        ScoreFormat.MUSICXML, source.replace('times="2"', 'times="3"').encode()
    )
    (entry,) = compare_music(before, after, ())
    assert entry["before_labels"] == ("9",)
    assert entry["changes"] == ["barline"]


@pytest.mark.anyio
async def test_reports_attribute_edit_only_in_the_measure_where_it_occurs() -> None:
    source = _SCORE.replace(
        "<divisions>4</divisions>", "<divisions>4</divisions><key><fifths>0</fifths></key>"
    ).replace(
        "</measure></part>",
        '</measure><measure number="10"><note><rest/><duration>4</duration></note>'
        "</measure></part>",
    )
    reader = MusicXmlScoreReader()
    before = await reader.read(ScoreFormat.MUSICXML, source.encode())
    after = await reader.read(ScoreFormat.MUSICXML, source.replace("fifths>0", "fifths>1").encode())
    assert before.parts[0].measures[1].opening != after.parts[0].measures[1].opening

    (entry,) = compare_music(before, after, ())
    assert entry["before_labels"] == ("9",)
    assert entry["changes"] == ["key"]


@pytest.mark.anyio
async def test_ambiguous_and_explicit_matching() -> None:
    reader = MusicXmlScoreReader()
    plain = await reader.read(ScoreFormat.MUSICXML, _SCORE.encode())
    original = plain.parts[0]
    second = replace(original.measures[0], position=2)
    duplicate = replace(plain, parts=(replace(original, measures=(*original.measures, second)),))
    (ambiguity,) = compare_music(duplicate, duplicate, ())
    assert ambiguity["status"] == "ambiguous"
    assert ambiguity["before"] == (1, 2)
    with pytest.raises(ScoreSelectionError, match="ambiguous"):
        read_range(duplicate.parts[0], "9", 2)
    assert (
        list(compare_music(duplicate, duplicate, (PartMatch(Match(1, 1), (Match(1, 1),)),))) == []
    )
    with pytest.raises(ScoreComparisonError, match="existing positions once"):
        list(compare_music(plain, plain, (PartMatch(Match(1, 2)),)))
