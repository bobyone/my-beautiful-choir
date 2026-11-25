# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Resolve measure-range selections by label or stable part-local position."""

from my_beautiful_choir.scores.reading.errors import ScoreSelectionError

type Selector = int | str


def select_position(entries: dict[int, str], requested: Selector, /, *, element: str) -> int:
    """Resolve a position or exact label, with actionable errors."""
    if isinstance(requested, int) and requested in entries:
        return requested
    if isinstance(requested, str):
        choices = [index for index, label in entries.items() if label == requested]
        if len(choices) == 1:
            return choices[0]
        if choices:
            listed = ", ".join(str(index) for index in choices[:20])
            suffix = " and more" if len(choices) > 20 else ""
            raise ScoreSelectionError(f"The {element} is ambiguous. Use position {listed}{suffix}.")
    raise ScoreSelectionError(f"The {element} was not found. Describe the score to locate it.")
