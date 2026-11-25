# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Normalise MusicXML measures onto an exact, part-wide timeline."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from xml.etree.ElementTree import Element

from my_beautiful_choir.scores.reading.errors import ScoreReadingError
from my_beautiful_choir.scores.reading.measure import Measure
from my_beautiful_choir.scores.reading.musical_event import MusicalEvent
from my_beautiful_choir.scores.reading.musicxml.details import (
    GRAPHICAL_ELEMENTS,
    notation,
    properties,
)
from my_beautiful_choir.scores.reading.musicxml.musicxml_pitch import read_pitch, sounding_pitch
from my_beautiful_choir.scores.reading.musicxml.numbers import decimal
from my_beautiful_choir.scores.reading.notation import Notation

_ZERO = Fraction(0)
_ATTRIBUTES = {"key", "time", "clef", "transpose", "staves", "staff-details", "measure-style"}
_POSITIONED = {"direction", "harmony", "figured-bass", "barline", "sound", "grouping"}
_NOTE_FIELDS = {"pitch", "duration", "voice", "staff", "instrument"}


class MeasureReader:
    """Read each measure in one part while carrying its attributes forward."""

    def __init__(self, instruments: dict[str, int], *, concert: bool) -> None:
        self._instruments = instruments
        self._concert = concert
        self._divisions = Fraction(1)
        self._active: dict[tuple[str, str | None], MusicalEvent] = {}

    def read(self, position: int, framing: Element[str], content: Element[str]) -> Measure:
        """Read a measure from either organisation of a MusicXML document."""
        cursor = _ZERO
        last_onset: Fraction | None = None
        unsupported: set[str] = set()
        events: list[MusicalEvent] = []
        changes: list[MusicalEvent] = []
        opening = tuple(self._active.values())
        for element in content:
            kind = element.tag
            if kind == "attributes":
                changes.extend(self._attributes(element, cursor, unsupported))
            elif kind == "note":
                in_chord = element.find("chord") is not None
                if in_chord and last_onset is None:
                    raise ScoreReadingError("A chord has no preceding note in this measure.")
                onset = last_onset if in_chord and last_onset is not None else cursor
                event = self._note(element, onset, unsupported)
                events.append(event)
                if not in_chord:
                    last_onset = onset
                    if event.duration is not None:
                        cursor = _bounded(cursor + event.duration)
            elif kind in {"backup", "forward"}:
                distance = self._duration(element)
                cursor = _bounded(cursor + distance if kind == "forward" else cursor - distance)
                if cursor < 0:
                    raise ScoreReadingError("A timing change moves before the start of a measure.")
                last_onset = None
            elif kind in _POSITIONED:
                if marker := self._marking(element, cursor, unsupported):
                    events.append(marker)
            elif kind not in GRAPHICAL_ELEMENTS:
                unsupported.add(kind)

        effective = list(opening)
        if len(changes) + len(opening) > 512:
            raise ScoreReadingError("A measure exceeds the limit for effective attribute changes.")
        for change in sorted(changes, key=lambda event: event.offset):
            key = change.kind, change.staff
            prior = self._active.get(key)
            next_value = replace(change, offset=_ZERO)
            scoped = (
                [item for item in self._active if item[0] == change.kind and item[1] is not None]
                if change.staff is None
                else []
            )
            if prior != next_value or scoped:
                for item in scoped:
                    del self._active[item]
                self._active[key] = next_value
                effective.append(change)
                events.append(change)
        if framing.get("non-controlling") == "yes":
            unsupported.add("non-controlling-measure")
        resolved = (
            replace(event, sounding=sounding_pitch(event, effective, concert=self._concert))
            if event.pitch is not None
            else event
            for event in events
        )
        # Serialise independent voices and staves consistently, preserving each voice's order.
        return Measure(
            position=position,
            label=framing.get("number", ""),
            opening=tuple(sorted(opening, key=lambda event: (event.kind, event.staff or ""))),
            events=tuple(sorted(resolved, key=_event_key)),
            implicit=framing.get("implicit") == "yes",
            unsupported=tuple(sorted(unsupported)),
        )

    def _attributes(
        self, element: Element[str], offset: Fraction, unsupported: set[str]
    ) -> list[MusicalEvent]:
        output = []
        for child in element:
            if child.tag == "divisions":
                value = decimal(child.text)
                if value <= 0:
                    raise ScoreReadingError("Musical divisions must be positive.")
                self._divisions = value
            elif child.tag in _ATTRIBUTES:
                detail = notation(child, unsupported)
                if detail is not None:
                    output.append(
                        MusicalEvent(child.tag, offset, child.get("number"), details=(detail,))
                    )
            elif child.tag not in GRAPHICAL_ELEMENTS:
                unsupported.add(child.tag)
        return output

    def _duration(self, element: Element[str]) -> Fraction:
        duration = _bounded(decimal(element.findtext("duration")) / self._divisions)
        if duration <= 0:
            raise ScoreReadingError("Musical durations must be positive.")
        return duration

    def _note(self, element: Element[str], offset: Fraction, unsupported: set[str]) -> MusicalEvent:
        pitch = element.find("pitch")
        rest = element.find("rest")
        unpitched = element.find("unpitched")
        duration = None if element.find("grace") is not None else self._duration(element)
        if sum(item is not None for item in (pitch, rest, unpitched)) != 1:
            raise ScoreReadingError(
                "A musical event must have a pitch, be unpitched, or be a rest."
            )
        details = []
        note_properties = properties(element)
        if note_properties:
            details.append(Notation("note-properties", properties=note_properties))
        if rest is not None:
            rest_properties = properties(rest)
            if rest_properties:
                details.append(Notation("rest-properties", properties=rest_properties))
        for child in element:
            if child.tag == "rest":
                for display in child:
                    if (detail := notation(display, unsupported)) is not None:
                        details.append(detail)
            elif child.tag == "instrument":
                instrument = child.get("id", "")
                if instrument in self._instruments:
                    details.append(Notation("instrument", str(self._instruments[instrument])))
                else:
                    unsupported.add("instrument-reference")
            elif (
                child.tag not in _NOTE_FIELDS
                and (detail := notation(child, unsupported)) is not None
            ):
                details.append(detail)
        return MusicalEvent(
            kind="rest" if rest is not None else "note",
            offset=offset,
            staff=element.findtext("staff", "1"),
            voice=element.findtext("voice", "1"),
            duration=duration,
            pitch=read_pitch(pitch) if pitch is not None else None,
            details=tuple(details),
        )

    def _marking(
        self, element: Element[str], offset: Fraction, unsupported: set[str]
    ) -> MusicalEvent | None:
        detail = notation(element, unsupported)
        if detail is None:
            return None
        if (delta := element.findtext("offset")) is not None:
            offset = _bounded(offset + decimal(delta) / self._divisions)
        musical_details = tuple(
            item for item in detail.details if item.kind not in {"offset", "staff", "voice"}
        )
        return MusicalEvent(
            element.tag,
            offset,
            element.findtext("staff"),
            element.findtext("voice"),
            details=(replace(detail, details=musical_details),),
        )


def _event_key(event: MusicalEvent) -> tuple[Fraction, str, str]:
    return event.offset, event.staff or "", event.voice or ""


def _bounded(value: Fraction) -> Fraction:
    if abs(value) > 1_000_000 or value.denominator.bit_length() > 128:
        raise ScoreReadingError("A musical time exceeds the reading limit.")
    return value
