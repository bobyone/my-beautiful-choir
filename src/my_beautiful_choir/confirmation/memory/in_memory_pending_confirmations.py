# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Pending confirmations kept in the memory of the process."""

import secrets
from datetime import datetime, timedelta

from my_beautiful_choir.clock.clock import Clock
from my_beautiful_choir.confirmation.errors import ConfirmationExpiredError
from my_beautiful_choir.confirmation.pending_confirmations import PendingConfirmations

DEFAULT_LIFETIME = timedelta(minutes=10)
TOKEN_BYTES = 32


class InMemoryPendingConfirmations[ActionT](PendingConfirmations[ActionT]):
    """Actions kept in a dictionary, lost when the server stops, which only cancels them.

    Tokens are random (``secrets``, 32 bytes) and valid for ``lifetime``;
    expired ones are forgotten whenever an action is kept.
    """

    def __init__(self, clock: Clock, lifetime: timedelta = DEFAULT_LIFETIME) -> None:
        self._clock = clock
        self._lifetime = lifetime
        self._pending: dict[str, tuple[datetime, ActionT]] = {}

    def keep(self, action: ActionT) -> str:
        now = self._clock.now()
        self._pending = {token: entry for token, entry in self._pending.items() if entry[0] > now}
        token = secrets.token_urlsafe(TOKEN_BYTES)
        self._pending[token] = (now + self._lifetime, action)
        return token

    def take(self, token: str) -> ActionT:
        entry = self._pending.pop(token, None)
        if entry is None or entry[0] <= self._clock.now():
            raise ConfirmationExpiredError
        return entry[1]
