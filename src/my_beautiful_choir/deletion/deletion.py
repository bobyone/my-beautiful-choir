# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Deletion value objects."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class DeletionTarget(StrEnum):
    """Kind of element a deletion removes."""

    CHOIR = "choir"
    WORK = "work"
    SCORE = "score"


@dataclass(frozen=True)
class Deletion:
    """What a deletion removes: an element and everything it contains."""

    target: DeletionTarget
    target_id: UUID
    name: str
    """Name of the choir, title of the work or label of the score."""
    parent_name: str | None = None
    """Name of the choir of a work, or title of the work of a score."""
    work_count: int = 0
    """Number of works deleted with a choir."""
    score_count: int = 0
    """Number of scores deleted with a choir or a work."""
    movement_number: int | None = None
    """Movement number of a score from a multi-movement transcription."""
    added_at: datetime | None = None
    """When that movement was published, to distinguish separate transcriptions."""
