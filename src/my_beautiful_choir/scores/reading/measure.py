# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""A measure and the attributes effective on its timeline."""

from dataclasses import dataclass

from my_beautiful_choir.scores.reading.musical_event import MusicalEvent


@dataclass(frozen=True)
class Measure:
    """A measure has a 1-based position and a potentially repeated printed label."""

    position: int
    label: str
    opening: tuple[MusicalEvent, ...]
    events: tuple[MusicalEvent, ...]
    implicit: bool = False
    unsupported: tuple[str, ...] = ()
