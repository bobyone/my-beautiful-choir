# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""The state covered by a deletion confirmation."""

from dataclasses import dataclass

from my_beautiful_choir.choirs.choir import Choir
from my_beautiful_choir.deletion.deletion import Deletion
from my_beautiful_choir.repertoire.work import Work
from my_beautiful_choir.scores.score import Score


@dataclass(frozen=True)
class DeletionPreview:
    """The displayed summary and the canonical state of the affected elements."""

    deletion: Deletion
    choir: Choir | None = None
    works: tuple[Work, ...] = ()
    scores: tuple[Score, ...] = ()
