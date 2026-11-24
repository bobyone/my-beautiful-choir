# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Errors from local score recognition."""

from my_beautiful_choir.errors import DomainError

AUDIVERIS_INSTALL_URL = "https://audiveris.github.io/audiveris/_pages/tutorials/install/binaries/"


class RecognitionError(DomainError):
    """Recognition failed without creating a score."""

    code = "failed"


class EngineNotFoundError(RecognitionError):
    """Audiveris was not found."""

    code = "engine_missing"

    def __init__(self) -> None:
        super().__init__(f"Install Audiveris and try again. {AUDIVERIS_INSTALL_URL}")


class EngineUnavailableError(RecognitionError):
    """Audiveris was found but did not start."""

    code = "engine_unavailable"

    def __init__(self) -> None:
        super().__init__(
            f"Check your Audiveris installation and try again. {AUDIVERIS_INSTALL_URL}"
        )


class UnsupportedSourceScoreError(RecognitionError):
    """The selected source score is not a PDF."""


class TranscriptionNotFoundError(RecognitionError):
    """The requested transcription status is unavailable."""
