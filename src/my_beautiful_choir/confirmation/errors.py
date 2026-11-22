# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Exceptions of the confirmation notion."""

from my_beautiful_choir.errors import DomainError


class ConfirmationError(DomainError):
    """Base class of the errors related to confirmations."""


class ConfirmationExpiredError(ConfirmationError):
    """A confirmation token is unknown, already used or expired."""

    def __init__(self) -> None:
        super().__init__(
            "This confirmation has expired or was already used: nothing was done. "
            "Ask for the action again."
        )
