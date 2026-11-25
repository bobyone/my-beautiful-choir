# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Score repository abstraction."""

import builtins
from abc import ABC, abstractmethod
from collections.abc import Collection
from uuid import UUID

from my_beautiful_choir.scores.score import Score


class ScoreRepository(ABC):
    """Stores the scores (not their content); used within a unit of work."""

    @abstractmethod
    async def add(self, score: Score) -> Score:
        """Add a new score, assigning a version number if it is final."""

    @abstractmethod
    async def finalise(self, score: Score) -> Score:
        """Finalise the expected draft revision and return its assigned version."""

    @abstractmethod
    async def get(self, score_id: UUID) -> Score:
        """Return the score with this id.

        Raises:
            ScoreNotFoundError: if there is none.
        """

    @abstractmethod
    async def list(self, work_id: UUID) -> list[Score]:
        """Scores of the work, the oldest first."""

    @abstractmethod
    async def list_transcriptions(self, run_id: int) -> builtins.list[Score]:
        """The remaining scores of a transcription run in movement order."""

    @abstractmethod
    async def list_of_choir(self, choir_id: UUID) -> builtins.list[Score]:
        """All scores of the choir."""

    @abstractmethod
    async def counts_of_works(self, work_ids: Collection[UUID]) -> dict[UUID, int]:
        """Number of scores of each given work. Omit works without scores."""

    @abstractmethod
    async def delete(self, score_id: UUID) -> None:
        """Delete a score (not its stored content)."""

    @abstractmethod
    async def storage_keys_of_work(self, work_id: UUID) -> builtins.list[str]:
        """Storage keys of the scores of the work, to delete their content with it."""

    @abstractmethod
    async def storage_keys_of_choir(self, choir_id: UUID) -> builtins.list[str]:
        """Storage keys of the scores of every work of the choir."""
