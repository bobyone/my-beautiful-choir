# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""An event placed on a measure's exact timeline."""

from dataclasses import dataclass
from fractions import Fraction

from my_beautiful_choir.scores.reading.notation import Notation
from my_beautiful_choir.scores.reading.pitch import Pitch


@dataclass(frozen=True)
class MusicalEvent:
    """A note, rest or marking attached to a staff and/or voice."""

    kind: str
    offset: Fraction
    staff: str | None = None
    voice: str | None = None
    duration: Fraction | None = None
    pitch: Pitch | None = None
    details: tuple[Notation, ...] = ()
    sounding: tuple[Fraction, ...] | None = None
