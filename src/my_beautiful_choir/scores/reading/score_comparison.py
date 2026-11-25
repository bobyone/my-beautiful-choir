# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Compare the parts and measures of two musical scores."""

from collections.abc import Iterator

from my_beautiful_choir.scores.reading.match import Match
from my_beautiful_choir.scores.reading.matching import matches
from my_beautiful_choir.scores.reading.measure_comparison import measure_changes
from my_beautiful_choir.scores.reading.part import Part
from my_beautiful_choir.scores.reading.part_match import PartMatch
from my_beautiful_choir.scores.reading.score_music import ScoreMusic


def compare_music(
    before: ScoreMusic, after: ScoreMusic, explicit: tuple[PartMatch, ...]
) -> Iterator[dict[str, object]]:
    """Yield changes, ambiguities and unsupported content in deterministic order."""
    old = {part.position: part for part in before.parts}
    new = {part.position: part for part in after.parts}
    override = {item.parts: item.measures for item in explicit}
    for status, left, right in matches(
        {number: part.label for number, part in old.items()},
        {number: part.label for number, part in new.items()},
        (item.parts for item in explicit),
    ):
        record: dict[str, object] = {
            "kind": "part",
            "status": status,
            "before": left,
            "after": right,
            "before_labels": tuple(old[index].label for index in left),
            "after_labels": tuple(new[index].label for index in right),
        }
        if status != "matched":
            yield record
            continue
        before_part, after_part = old[left[0]], new[right[0]]
        pair = Match(left[0], right[0])
        changes = []
        if before_part.label != after_part.label:
            changes.append("label")
        if before_part.instruments != after_part.instruments:
            changes.append("instruments")
        if changes:
            yield {**record, "status": "changed", "changes": changes}
        yield from _compare_part(before_part, after_part, override.get(pair, ()))

    for side, music in (("before", before), ("after", after)):
        for feature in music.unsupported:
            yield {"kind": "unsupported", "side": side, "feature": feature}
        for part in music.parts:
            for measure in part.measures:
                for feature in measure.unsupported:
                    yield {
                        "kind": "unsupported",
                        "side": side,
                        "part": part.position,
                        "measure": measure.position,
                        "feature": feature,
                    }


def _compare_part(
    before: Part, after: Part, explicit: tuple[Match, ...]
) -> Iterator[dict[str, object]]:
    old = {measure.position: measure for measure in before.measures}
    new = {measure.position: measure for measure in after.measures}
    for status, left, right in matches(
        {index: measure.label for index, measure in old.items()},
        {index: measure.label for index, measure in new.items()},
        explicit,
    ):
        record = {
            "kind": "measure",
            "before_part": before.position,
            "after_part": after.position,
            "before": left,
            "after": right,
            "before_labels": tuple(old[index].label for index in left),
            "after_labels": tuple(new[index].label for index in right),
        }
        if status != "matched":
            yield {**record, "status": status}
            continue
        first, second = old[left[0]], new[right[0]]
        changes = measure_changes(first, second)
        if first.label != second.label:
            changes.append("label")
        if changes:
            yield {**record, "status": "changed", "changes": changes}
