# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""An explicit part match and its optional measure matches."""

from dataclasses import dataclass

from my_beautiful_choir.scores.reading.match import Match


@dataclass(frozen=True)
class PartMatch:
    """Associate two parts and provide explicit matches for any of their measures."""

    parts: Match
    measures: tuple[Match, ...] = ()
