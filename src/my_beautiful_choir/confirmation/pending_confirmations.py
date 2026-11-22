# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Pending confirmations abstraction."""

from abc import ABC, abstractmethod


class PendingConfirmations[ActionT](ABC):
    """Keeps actions awaiting the user's confirmation in a view, under single-use tokens.

    Used when the user cannot be asked during the tool call: the view shows
    the action and sends the token back when the user confirms it.
    """

    @abstractmethod
    def keep(self, action: ActionT) -> str:
        """Keep ``action`` and return its token: unguessable, single use, valid for a while."""

    @abstractmethod
    def take(self, token: str) -> ActionT:
        """Return the action of ``token`` and forget it, so that it is done at most once.

        Raises:
            ConfirmationExpiredError: if the token is unknown, already used or expired.
        """
