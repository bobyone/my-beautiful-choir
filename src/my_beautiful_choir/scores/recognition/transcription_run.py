# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""A completed transcription and its expected number of movements."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class TranscriptionRun:
    """A published run, kept even if some or all of its scores are deleted."""

    id: int
    work_id: UUID
    source_score_id: UUID
    movement_count: int
