# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Outcome of a confirmation request."""

from enum import StrEnum


class ConfirmationOutcome(StrEnum):
    """Answer to a confirmation request."""

    CONFIRMED = "confirmed"
    """The user confirmed the action."""

    REFUSED = "refused"
    """The user refused or dismissed the request: the action must not be done."""

    UNAVAILABLE = "unavailable"
    """The user could not be asked (the client cannot ask questions)."""
