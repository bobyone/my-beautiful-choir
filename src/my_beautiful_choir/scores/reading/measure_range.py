# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Select a contiguous range and retain indications across its boundaries."""

from collections import defaultdict
from collections.abc import Iterator

from my_beautiful_choir.scores.reading.errors import ScoreSelectionError
from my_beautiful_choir.scores.reading.notation_span import NotationSpan
from my_beautiful_choir.scores.reading.notation_spans import notation_spans
from my_beautiful_choir.scores.reading.part import Part
from my_beautiful_choir.scores.reading.selections import Selector, select_position


def read_range(
    part: Part, start: Selector, end: Selector
) -> tuple[int, Iterator[dict[str, object]]]:
    """Read measures with effective opening attributes and spanning indications."""
    positions = {measure.position: measure.label for measure in part.measures}
    first = select_position(positions, start, element="start measure")
    last = select_position(positions, end, element="end measure")
    if first > last:
        raise ScoreSelectionError("The start measure must precede or equal the end measure.")
    return first, _with_boundaries(part, first, last)


def _with_boundaries(part: Part, first: int, last: int) -> Iterator[dict[str, object]]:
    starts: dict[int, list[tuple[int, NotationSpan]]] = defaultdict(list)
    ends: dict[int, list[int]] = defaultdict(list)
    active: dict[int, NotationSpan] = {}
    for index, span in enumerate(notation_spans(part)):
        if not span.start or not span.end or span.start.measure == span.end.measure:
            continue
        if span.end.measure < first or span.start.measure > last:
            continue
        ends[span.end.measure].append(index)
        if span.start.measure < first:
            active[index] = span
        else:
            starts[span.start.measure].append((index, span))
    for measure in part.measures[first - 1 : last]:
        position = measure.position
        incoming = tuple(active.values())
        for index in ends.get(position, ()):
            active.pop(index)
        active.update(starts.get(position, ()))
        yield {
            "position": position,
            "label": measure.label,
            "implicit": measure.implicit,
            "opening": measure.opening,
            "events": measure.events,
            "incoming": incoming,
            "outgoing": tuple(active.values()),
            "unsupported": measure.unsupported,
        }
