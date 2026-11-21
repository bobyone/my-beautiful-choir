# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Unit of Work abstraction."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from types import TracebackType
from typing import Self

from my_beautiful_choir.choirs.choir_repository import ChoirRepository
from my_beautiful_choir.repertoire.work_repository import WorkRepository
from my_beautiful_choir.scores.score_repository import ScoreRepository


class UnitOfWork(ABC):
    """One atomic operation on the data store, giving access to the repositories.

    Used as an asynchronous context: changes are kept only when ``commit`` is
    called; leaving the context without committing, or with an exception,
    discards them.
    """

    @abstractmethod
    async def __aenter__(self) -> Self:
        """Start the operation."""

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """End the operation, discarding uncommitted changes."""

    @property
    @abstractmethod
    def choirs(self) -> ChoirRepository:
        """Repository of the choirs."""

    @property
    @abstractmethod
    def works(self) -> WorkRepository:
        """Repository of the works."""

    @property
    @abstractmethod
    def scores(self) -> ScoreRepository:
        """Repository of the scores."""

    @abstractmethod
    async def commit(self) -> None:
        """Keep the changes made so far."""


type UnitOfWorkFactory = Callable[[], UnitOfWork]
"""Creates a new unit of work for each operation."""
