# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Contract for a local optical music recognition engine."""

from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager

from my_beautiful_choir.scores.sources.score_source import ScoreSource


class ScoreRecognizer(ABC):
    """Transcribe a complete source PDF into ordered MusicXML movements."""

    @abstractmethod
    def transcribe(self, pdf: bytes) -> AbstractAsyncContextManager[tuple[ScoreSource, ...]]:
        """Provide the movement sources while their workspace is open.

        Raise RecognitionError for an unusable or incomplete export.
        """
