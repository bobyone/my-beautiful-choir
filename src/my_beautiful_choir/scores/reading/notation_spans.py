# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Find notation that crosses measure boundaries or has missing endpoints."""

from collections import defaultdict
from collections.abc import Iterator
from fractions import Fraction

from my_beautiful_choir.scores.reading.event_location import EventLocation
from my_beautiful_choir.scores.reading.musical_event import MusicalEvent
from my_beautiful_choir.scores.reading.notation_details import walk_notation
from my_beautiful_choir.scores.reading.notation_span import NotationSpan
from my_beautiful_choir.scores.reading.part import Part

_SPANNING = {
    "tied",
    "tie",
    "slur",
    "wedge",
    "octave-shift",
    "pedal",
    "wavy-line",
    "glissando",
    "slide",
    "bracket",
    "dashes",
}
_START = {"start", "crescendo", "diminuendo", "up", "down", "sostenuto"}
_STOP = {"stop", "discontinue"}

type _Key = tuple[str, str, Fraction | None]
type _Start = tuple[EventLocation, tuple[str | None, str | None]]


def _endpoints(event: MusicalEvent) -> Iterator[tuple[_Key, str]]:
    details = tuple(walk_notation(event.details))
    has_notated_tie = any(item.kind == "tied" for item in details)
    for item in details:
        if item.kind == "lyric":
            for detail in item.details:
                action = dict(detail.properties).get("type", "")
                if detail.kind == "extend" and action in {"start", "stop"}:
                    verse = dict(item.properties).get("number", "1")
                    yield ("melisma", repr((event.staff, event.voice, verse)), None), action
        if item.kind not in _SPANNING or (item.kind == "tie" and has_notated_tie):
            continue
        properties = dict(item.properties)
        action = properties.get("type", "")
        kind = "tie" if item.kind == "tied" else item.kind
        height = event.pitch.height if event.pitch and kind == "tie" else None
        key = kind, properties.get("number", "1") if kind != "tie" else "1", height
        if action == "continue" and kind == "tie":
            yield key, "stop"
            yield key, "start"
        elif action in _START | _STOP:
            yield key, action


def _select_start(pending: list[_Start], owner: tuple[str | None, str | None]) -> int | None:
    for index in range(len(pending) - 1, max(-1, len(pending) - 65), -1):
        if pending[index][1] == owner:
            return index
    return 0 if len(pending) == 1 else None


def notation_spans(part: Part) -> tuple[NotationSpan, ...]:
    """Match endpoints in one part, including ties across voices when unambiguous."""
    pending: dict[_Key, list[_Start]] = defaultdict(list)
    results = []
    for measure in part.measures:
        for index, event in enumerate(measure.events, 1):
            location = EventLocation(measure.position, index)
            owner = event.staff, event.voice
            endpoints = sorted(_endpoints(event), key=lambda endpoint: endpoint[1] not in _STOP)
            for key, action in endpoints:
                candidates = pending[key]
                if action in _START:
                    candidates.append((location, owner))
                else:
                    match = _select_start(candidates, owner)
                    start = candidates.pop(match)[0] if match is not None else None
                    results.append(NotationSpan(key[0], start, location))
    for key, starts in pending.items():
        results.extend(NotationSpan(key[0], start) for start, _ in starts)
    return tuple(results)
