# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Describe and select measures from an injected musical model."""

from dataclasses import replace
from fractions import Fraction

from my_beautiful_choir.scores.reading.measure import Measure
from my_beautiful_choir.scores.reading.measure_range import read_range
from my_beautiful_choir.scores.reading.musical_event import MusicalEvent
from my_beautiful_choir.scores.reading.notation import Notation
from my_beautiful_choir.scores.reading.part import Part
from my_beautiful_choir.scores.reading.pitch import Pitch
from my_beautiful_choir.scores.reading.score_description import describe_music
from my_beautiful_choir.scores.reading.score_music import ScoreMusic


def test_describes_anomalies_without_flagging_anacrusis_and_unmetered_music() -> None:
    start = Fraction(0)
    time = MusicalEvent(
        "time",
        start,
        details=(Notation("time", details=(Notation("beats", "4"), Notation("beat-type", "4"))),),
    )
    unmetered = replace(time, details=(Notation("time", details=(Notation("senza-misura"),)),))
    note = MusicalEvent("note", start, "1", "1", Fraction(1), Pitch("C", 4, start))
    pickup = replace(note, details=(Notation("tied", properties=(("type", "start"),)),))
    complete_tie = replace(
        note,
        details=(
            Notation("tied", properties=(("type", "stop"),)),
            Notation("lyric", properties=(("number", "2"),)),
        ),
    )
    incomplete_slur = replace(note, details=(Notation("slur", properties=(("type", "start"),)),))
    part = Part(
        1,
        "Voice",
        (),
        (
            Measure(1, "0", (), (time, pickup), implicit=True),
            Measure(2, "1", (time,), (complete_tie,)),
            Measure(3, "2", (time,), (unmetered, incomplete_slur)),
        ),
    )
    report = list(describe_music(ScoreMusic((part,))))
    assert [
        (entry["measure"], entry["code"]) for entry in report if entry["kind"] == "detected_anomaly"
    ] == [(2, "incomplete_measure"), (3, "open_slur")]
    assert [entry["verse"] for entry in report if entry["kind"] == "verse"] == ["2"]
    _, records = read_range(part, "1", "1")
    (record,) = records
    assert record["opening"] == (time,)
    assert record["incoming"]
    assert not record["outgoing"]
