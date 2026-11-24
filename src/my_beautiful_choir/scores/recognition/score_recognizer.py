# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Contract for a local optical music recognition engine."""

from abc import ABC, abstractmethod


class ScoreRecognizer(ABC):
    """Transcribe a complete source PDF to a single MusicXML document."""

    @abstractmethod
    async def transcribe(self, pdf: bytes) -> bytes:
        """Return MusicXML, or raise RecognitionError for an unusable or incomplete result."""
