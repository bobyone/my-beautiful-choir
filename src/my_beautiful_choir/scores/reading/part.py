# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""An ordered part and its declared instruments."""

from dataclasses import dataclass

from my_beautiful_choir.scores.reading.measure import Measure
from my_beautiful_choir.scores.reading.notation import Notation


@dataclass(frozen=True)
class Part:
    """A part with an identity by position within its score."""

    position: int
    label: str
    instruments: tuple[Notation, ...]
    measures: tuple[Measure, ...]
