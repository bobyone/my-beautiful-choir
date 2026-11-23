# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Repertoire page: an ordered slice of the works of a choir matching a search."""

from dataclasses import dataclass
from uuid import UUID

from my_beautiful_choir.choirs.choir import Choir
from my_beautiful_choir.repertoire.errors import InvalidRepertoirePageError
from my_beautiful_choir.repertoire.work import Work

DEFAULT_PAGE_SIZE = 10
MAXIMUM_PAGE_SIZE = 100


@dataclass(frozen=True, slots=True)
class PageRequest:
    """Requested page number (from 1) and page size (1 to ``MAXIMUM_PAGE_SIZE``)."""

    number: int = 1
    size: int = DEFAULT_PAGE_SIZE

    def __post_init__(self) -> None:
        if self.number < 1:
            raise InvalidRepertoirePageError("the page number must be at least 1")
        if not 1 <= self.size <= MAXIMUM_PAGE_SIZE:
            raise InvalidRepertoirePageError(
                f"the page size must be between 1 and {MAXIMUM_PAGE_SIZE}"
            )


def page_count(work_count: int, size: int) -> int:
    """Number of pages holding ``work_count`` works; an empty repertoire has one page."""
    return max(1, -(-work_count // size))


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
