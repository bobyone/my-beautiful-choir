# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Confirmation requester abstraction."""

from abc import ABC, abstractmethod
from collections.abc import Callable

from my_beautiful_choir.confirmation.confirmation_outcome import ConfirmationOutcome


class ConfirmationRequester(ABC):
    """Asks the user to confirm an action, during the current tool call."""

    def resume(self, scope: str) -> tuple[str, ConfirmationOutcome] | None:
        """Return the token and answer from a continuation of the given call."""
        return None

    @abstractmethod
    async def ask(
        self, question: str, *, scope: str = "", keep: Callable[[], str] | None = None
    ) -> ConfirmationOutcome:
        """Ask ``question`` (English, self-sufficient) and return the user's answer.

        Never raises because the user cannot be asked: returns ``UNAVAILABLE``
        instead.
        """
