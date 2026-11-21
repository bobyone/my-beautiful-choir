# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Confirmation requester abstraction."""

from abc import ABC, abstractmethod

from my_beautiful_choir.confirmation.confirmation_outcome import ConfirmationOutcome


class ConfirmationRequester(ABC):
    """Asks the user to confirm an action, during the current tool call."""

    @abstractmethod
    async def ask(self, question: str) -> ConfirmationOutcome:
        """Ask ``question`` (English, self-sufficient) and return the user's answer.

        Never raises because the user cannot be asked: returns ``UNAVAILABLE``
        instead.
        """
