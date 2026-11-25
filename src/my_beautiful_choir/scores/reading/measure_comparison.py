# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Compare the musical content of matched measures."""

from collections import defaultdict
from collections.abc import Iterable

from my_beautiful_choir.scores.reading.measure import Measure
from my_beautiful_choir.scores.reading.musical_event import MusicalEvent
from my_beautiful_choir.scores.reading.notation import Notation

_CATEGORIES = {
    "lyric": "lyrics",
    "tied": "ties",
    "tie": "ties",
    "slur": "slurs",
    "dynamics": "dynamics",
    "wedge": "dynamics",
}
_CONTAINERS = {"notations", "direction", "direction-type"}
_ATTRIBUTES = {"time", "key", "clef", "transpose", "staves", "staff-details", "measure-style"}


def measure_changes(before: Measure, after: Measure) -> list[str]:
    """Name the musical categories that differ, without returning free text."""
    left, right = _categories(before), _categories(after)
    return sorted(kind for kind in left.keys() | right.keys() if left.get(kind) != right.get(kind))


def _categories(measure: Measure) -> dict[str, list[object]]:
    categories: dict[str, list[object]] = defaultdict(list)
    if measure.implicit:
        categories["measure_attributes"].append("implicit")
    categories["effective_attributes"].extend(measure.opening)
    for event in measure.events:
        position = event.offset, event.staff, event.voice
        if event.kind in {"note", "rest"}:
            categories["rhythm"].append((*position, event.kind, event.duration))
            if event.pitch:
                categories["pitch"].append((*position, event.pitch.height, event.sounding))
                categories["written_spelling"].append((*position, event.pitch))
        if event.kind in _ATTRIBUTES:
            categories[event.kind].append(event)
        else:
            for kind, notation in _details(event, event.details):
                categories[kind].append((*position, notation))
    return categories


def _details(event: MusicalEvent, details: Iterable[Notation]) -> Iterable[tuple[str, Notation]]:
    for detail in details:
        fallback = event.kind if event.kind not in {"note", "rest"} else "notation"
        if detail.kind in _CONTAINERS:
            if detail.value or detail.properties or not detail.details:
                yield fallback, Notation(detail.kind, detail.value, detail.properties)
            yield from _details(event, detail.details)
        else:
            yield _CATEGORIES.get(detail.kind, fallback), detail
