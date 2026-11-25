# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Written pitch and its exact sounding height, when supplied by the score."""

from dataclasses import dataclass
from fractions import Fraction

_SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


@dataclass(frozen=True)
class Pitch:
    """Written spelling with an alteration in semitones."""

    step: str
    octave: int
    alter: Fraction

    @property
    def height(self) -> Fraction:
        """Semitones relative to MIDI note zero, preserving microtones."""
        return 12 * (self.octave + 1) + _SEMITONES[self.step] + self.alter
