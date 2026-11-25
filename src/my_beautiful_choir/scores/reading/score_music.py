# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""The musical content read from a score."""

from dataclasses import dataclass

from my_beautiful_choir.scores.reading.part import Part


@dataclass(frozen=True)
class ScoreMusic:
    """Parts in score order and any unsupported score-level features."""

    parts: tuple[Part, ...]
    unsupported: tuple[str, ...] = ()
