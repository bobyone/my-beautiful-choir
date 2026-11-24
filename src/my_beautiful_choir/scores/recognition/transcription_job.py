# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""State of an in-process transcription."""

import asyncio
from dataclasses import dataclass
from uuid import UUID

from my_beautiful_choir.scores.recognition.errors import RecognitionError
from my_beautiful_choir.scores.score import Score


@dataclass
class TranscriptionJob:
    """A running transcription and its eventual outcome."""

    id: UUID
    source_id: UUID
    recompute: bool = False
    scores: tuple[Score, ...] = ()
    error: RecognitionError | None = None
    task: asyncio.Task[None] | None = None
