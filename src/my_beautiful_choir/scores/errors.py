# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Exceptions of the scores notion."""

from uuid import UUID

from my_beautiful_choir.errors import DomainError
from my_beautiful_choir.scores.formats.score_format import ScoreFormat

MEGABYTE = 1024 * 1024


class ScoresError(DomainError):
    """Base class of the errors related to the scores."""


class FinalScoreProtectedError(ScoresError):
    """The requested change would affect a final score."""

    def __init__(self) -> None:
        super().__init__("This score is final. Duplicate it as a draft to change it.")


class DraftScoreNotAllowedError(ScoresError):
    """This use requires a final score."""

    def __init__(self) -> None:
        super().__init__("This score is a draft. Finalise it or choose a final score.")


class ScoreNotDuplicableError(ScoresError):
    """The score cannot be duplicated as an editable draft."""

    def __init__(self) -> None:
        super().__init__("Choose a final MusicXML or compressed MusicXML score to duplicate.")


class StaleFinalisationError(ScoresError):
    """The reviewed draft is no longer current."""

    def __init__(self) -> None:
        super().__init__("The draft changed. Review it again before finalising.")


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


class InvalidScoreError(ScoresError):
    """An attribute of a score is invalid."""

    def __init__(self, attribute: str, reason: str) -> None:
        super().__init__(f"The {attribute} of the score is invalid: {reason}.")
        self.attribute = attribute
        self.reason = reason


class ScoreNotFoundError(ScoresError):
    """No score has the given id."""

    def __init__(self, score_id: UUID) -> None:
        super().__init__(
            f"No score has the id {score_id}. Show the work to find the id of its scores."
        )
        self.score_id = score_id


class ScoreFileMissingError(ScoresError):
    """The content of a score is missing from the file storage."""

    def __init__(self, score_id: UUID, label: str) -> None:
        super().__init__(
            f"The file of the score {label!r} is missing from the data directory. Restore it "
            "from a backup, or delete the score and add it again."
        )
        self.score_id = score_id
        self.label = label


class StoredScoreTooLargeError(ScoresError):
    """The stored file of a score is larger than the score maximum."""

    def __init__(self, score_id: UUID, label: str, limit: int) -> None:
        super().__init__(
            f"The file of the score {label!r} is larger than the {limit / MEGABYTE:g} MB "
            "maximum of a score: it was changed outside the application. Restore it from a "
            "backup, or delete the score and add it again."
        )
        self.score_id = score_id
        self.label = label
        self.limit = limit


class ScoreOpenError(ScoresError):
    """A score cannot be opened on the user's computer."""

    def __init__(self, score_format: ScoreFormat, reason: str) -> None:
        super().__init__(
            f"The score cannot be opened: {reason}. Check that an application opening "
            f"{score_format.display_name} files ({score_format.extension}) is installed."
        )
        self.format = score_format
        self.reason = reason
