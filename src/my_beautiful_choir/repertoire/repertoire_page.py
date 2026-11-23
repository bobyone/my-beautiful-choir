# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Repertoire page: an ordered slice of the works of a choir matching a search."""

from dataclasses import dataclass
from uuid import UUID

from my_beautiful_choir.choirs.choir import Choir
from my_beautiful_choir.repertoire.page_request import page_count
from my_beautiful_choir.repertoire.work import Work


@dataclass(frozen=True, slots=True)
class RepertoirePage:
    """Works of one page, ordered by title then composer, with their score totals.

    Invariant: ``1 <= number <= page_count``.
    """

    choir: Choir
    works: tuple[Work, ...]
    score_counts: dict[UUID, int]
    number: int
    size: int
    work_count: int

    @property
    def page_count(self) -> int:
        """Number of pages of the search."""
        return page_count(self.work_count, self.size)
