# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Exceptions of the scores notion."""

from my_beautiful_choir.errors import DomainError
from my_beautiful_choir.scores.formats.score_format import ScoreFormat

MEGABYTE = 1024 * 1024


class ScoresError(DomainError):
    """Base class of the errors related to the scores."""


class UnsupportedScoreFormatError(ScoresError):
    """The content of a file is not a score in a supported format."""

    def __init__(self) -> None:
        accepted = ", ".join(
            f"{format.display_name} ({format.extension})" for format in ScoreFormat
        )
        super().__init__(
            f"The file is not a score in a supported format. Accepted formats: {accepted}."
        )


class InvalidScoreSizeError(ScoresError):
    """The content of a score is empty or larger than the limit."""

    def __init__(self, limit: int) -> None:
        super().__init__(
            "The file is empty or too large: a score must hold between 1 byte and "
            f"{limit / MEGABYTE:g} MB."
        )
        self.limit = limit
