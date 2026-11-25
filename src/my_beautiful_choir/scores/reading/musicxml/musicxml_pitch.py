# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Read written pitch and calculate explicitly declared sounding pitch."""

from __future__ import annotations

from collections.abc import Iterable
from fractions import Fraction
from xml.etree.ElementTree import Element

from my_beautiful_choir.scores.reading.errors import ScoreReadingError
from my_beautiful_choir.scores.reading.musical_event import MusicalEvent
from my_beautiful_choir.scores.reading.musicxml.numbers import decimal, integer
from my_beautiful_choir.scores.reading.pitch import Pitch


def read_pitch(element: Element[str]) -> Pitch:
    """Read the written pitch without losing enharmonic spelling."""
    step = element.findtext("step")
    octave = integer(element.findtext("octave"))
    if step not in {"A", "B", "C", "D", "E", "F", "G"} or not -1 <= octave <= 10:
        raise ScoreReadingError("The score contains an invalid written pitch.")
    return Pitch(step, octave, decimal(element.findtext("alter", "0")))


def sounding_pitch(
    event: MusicalEvent, changes: Iterable[MusicalEvent], *, concert: bool
) -> tuple[Fraction, ...] | None:
    """Use transpose attributes effective at the note on the same staff."""
    if event.pitch is None:
        return None
    transpose = None
    for change in changes:
        if (
            change.kind == "transpose"
            and change.offset <= event.offset
            and (change.staff is None or change.staff == event.staff)
        ):
            transpose = change.details[0]
    if transpose is None:
        return (event.pitch.height,) if concert else None
    items = {detail.kind: detail for detail in transpose.details}
    if "chromatic" not in items:
        return None
    height = event.pitch.height + decimal(items["chromatic"].value)
    if "octave-change" in items:
        height += 12 * integer(items["octave-change"].value)
    if "double" in items:
        direction = 12 if dict(items["double"].properties).get("above") == "yes" else -12
        return (height, height + direction)
    return (height,)
