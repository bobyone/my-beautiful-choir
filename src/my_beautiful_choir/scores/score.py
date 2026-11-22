# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Score value object."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.score_origin import ScoreOrigin


@dataclass(frozen=True)
class Score:
    """File holding the written music of a work; its content is in the file storage."""

    id: UUID
    work_id: UUID
    label: str
    """Name distinguishing the score from the other scores of its work."""
    format: ScoreFormat
    size: int
    """Size of the content, in bytes."""
    original_name: str
    """Name of the file when it was added; metadata only, never used as a path."""
    origin: ScoreOrigin
    link: str | None
    """Public Google Drive link the score was downloaded from, if any."""
    storage_key: str
    """Key of the content in the file storage."""
    added_at: datetime
