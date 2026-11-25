# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Describe musical parts and report conservatively detected anomalies."""

from collections.abc import Iterator
from fractions import Fraction

from my_beautiful_choir.scores.reading.measure import Measure
from my_beautiful_choir.scores.reading.notation_details import walk_notation
from my_beautiful_choir.scores.reading.notation_spans import notation_spans
from my_beautiful_choir.scores.reading.part import Part
from my_beautiful_choir.scores.reading.score_music import ScoreMusic


def describe_music(music: ScoreMusic) -> Iterator[dict[str, object]]:
    """Yield small records in part order so a description can be paginated."""
    for feature in music.unsupported:
        yield {"kind": "unsupported", "feature": feature}
    for part in music.parts:
        yield {
            "kind": "part",
            "part": part.position,
            "label": part.label,
            "measure_count": len(part.measures),
        }
        for number, instrument in enumerate(part.instruments, 1):
            yield {
                "kind": "instrument",
                "part": part.position,
                "instrument": number,
                "notation": instrument,
            }
        yield from _describe_measures(part)
        yield from _spans_and_ranges(part)


def _describe_measures(part: Part) -> Iterator[dict[str, object]]:
    for measure in part.measures:
        location = {"part": part.position, "measure": measure.position, "label": measure.label}
        for feature in measure.unsupported:
            yield {"kind": "unsupported", **location, "feature": feature}
        for event in measure.events:
            if event.kind in {"time", "key"}:
                yield {"kind": event.kind, **location, "event": event}
        if anomaly := _duration_anomaly(measure, last=measure.position == len(part.measures)):
            yield {"kind": "detected_anomaly", **location, "code": anomaly}


def _spans_and_ranges(part: Part) -> Iterator[dict[str, object]]:
    written = [event.pitch for measure in part.measures for event in measure.events if event.pitch]
    if written:
        yield {
            "kind": "range",
            "part": part.position,
            "pitch_mode": "written",
            "lowest": min(written, key=lambda pitch: pitch.height),
            "highest": max(written, key=lambda pitch: pitch.height),
        }
    sounding = [
        pitch
        for measure in part.measures
        for event in measure.events
        for pitch in (event.sounding or ())
    ]
    if written:
        yield {
            "kind": "range",
            "part": part.position,
            "pitch_mode": "sounding",
            "lowest": str(min(sounding)) if sounding else None,
            "highest": str(max(sounding)) if sounding else None,
            "partial": any(
                event.pitch is not None and event.sounding is None
                for measure in part.measures
                for event in measure.events
            ),
        }
    verses = set()
    for measure in part.measures:
        for event in measure.events:
            for detail in walk_notation(event.details):
                if detail.kind == "lyric":
                    verses.add(
                        (dict(detail.properties).get("number", "1"), event.staff, event.voice)
                    )
    for verse, staff, voice in sorted(
        verses, key=lambda item: (item[0], item[1] or "", item[2] or "")
    ):
        yield {
            "kind": "verse",
            "part": part.position,
            "verse": verse,
            "staff": staff,
            "voice": voice,
        }
    for span in notation_spans(part):
        if (
            span.kind in {"tie", "slur"}
            and (span.start is None or span.end is None)
            and (location := span.start or span.end) is not None
        ):
            yield {
                "kind": "detected_anomaly",
                "part": part.position,
                "measure": location.measure,
                "event_position": location.event,
                "code": f"open_{span.kind}",
            }


def _duration_anomaly(measure: Measure, *, last: bool) -> str | None:
    if measure.implicit or measure.unsupported:
        return None
    times = [event for event in (*measure.opening, *measure.events) if event.kind == "time"]
    in_measure = [event for event in measure.events if event.kind == "time"]
    if not times or any(event.staff is not None or event.offset != 0 for event in in_measure):
        return None
    time = times[-1].details[0]
    if times[-1].staff is not None:
        return None
    beats = [item.value for item in time.details if item.kind == "beats"]
    units = [item.value for item in time.details if item.kind == "beat-type"]
    if not beats or len(beats) != len(units) or len(beats) > 32:
        return None
    try:
        expected = sum(
            (
                Fraction(4 * sum(int(beat) for beat in row.split("+")), int(unit))
                for row, unit in zip(beats, units, strict=True)
            ),
            Fraction(0),
        )
    except (ValueError, ZeroDivisionError):
        return None
    timed = [
        (event.staff, event.voice, event.offset, event.duration)
        for event in measure.events
        if event.duration is not None
    ]
    if not timed or expected <= 0:
        return None
    end = max(offset + duration for _, _, offset, duration in timed)
    if end > expected:
        return "overfull_measure"
    # Short first/last measures and gaps in secondary voices can be deliberate.
    if (
        measure.position > 1
        and not last
        and end < expected
        and len({(staff, voice) for staff, voice, _, _ in timed}) == 1
    ):
        return "incomplete_measure"
    return None
