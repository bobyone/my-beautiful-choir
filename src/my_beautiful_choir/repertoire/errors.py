# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Exceptions of the repertoire notion."""

from uuid import UUID

from my_beautiful_choir.errors import DomainError


class RepertoireError(DomainError):
    """Base class of the errors related to the repertoire."""


class WorkNotFoundError(RepertoireError):
    """No work has the given id."""

    def __init__(self, work_id: UUID) -> None:
        super().__init__(
            f"No work has the id {work_id}. Show the repertoire to find the id of the work."
        )
        self.work_id = work_id


class InvalidRepertoirePageError(RepertoireError):
    """The requested repertoire page number or size is out of bounds."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"The repertoire page is invalid: {reason}.")
        self.reason = reason


class InvalidWorkError(RepertoireError):
    """An attribute of the work is invalid."""

    def __init__(self, attribute: str, reason: str) -> None:
        super().__init__(f"The {attribute} of the work is invalid: {reason}.")
        self.attribute = attribute
        self.reason = reason
