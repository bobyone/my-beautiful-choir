# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Resolve explicit and automatically unambiguous part or measure matches."""

from collections import defaultdict
from collections.abc import Iterable, Iterator

from my_beautiful_choir.scores.reading.errors import ScoreComparisonError
from my_beautiful_choir.scores.reading.match import Match

type _Positions = dict[str, list[int]]


def matches(
    before: dict[int, str], after: dict[int, str], explicit: Iterable[Match]
) -> Iterator[tuple[str, tuple[int, ...], tuple[int, ...]]]:
    """Yield matched, added, removed or ambiguous positions in deterministic order."""
    remaining_before = dict(before)
    remaining_after = dict(after)
    for item in explicit:
        if item.before not in remaining_before or item.after not in remaining_after:
            raise ScoreComparisonError("Each explicit match must use existing positions once.")
        del remaining_before[item.before]
        del remaining_after[item.after]
        yield "matched", (item.before,), (item.after,)

    old = _by_label(remaining_before)
    new = _by_label(remaining_after)
    for label in dict.fromkeys([*old, *new]):
        left, right = tuple(old.get(label, [])), tuple(new.get(label, []))
        if not left:
            for item_after in right:
                yield "added", (), (item_after,)
        elif not right:
            for item_before in left:
                yield "removed", (item_before,), ()
        elif label and len(left) == len(right) == 1:
            yield "matched", left, right
        else:
            yield "ambiguous", left, right


def _by_label(elements: dict[int, str]) -> _Positions:
    result: _Positions = defaultdict(list)
    for position, label in elements.items():
        result[label].append(position)
    return result
