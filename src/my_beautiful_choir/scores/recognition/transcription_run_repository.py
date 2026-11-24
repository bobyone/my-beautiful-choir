# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Persistence contract for completed transcription runs."""

from abc import ABC, abstractmethod
from uuid import UUID

from my_beautiful_choir.scores.recognition.transcription_run import TranscriptionRun


class TranscriptionRunRepository(ABC):
    """Read and write transcription runs in the current unit of work."""

    @abstractmethod
    async def add(
        self, work_id: UUID, source_score_id: UUID, movement_count: int
    ) -> TranscriptionRun:
        """Record a run and return its assigned identifier."""

    @abstractmethod
    async def latest(self, source_score_id: UUID) -> TranscriptionRun | None:
        """Return the latest committed run, even if its scores have since been deleted."""
