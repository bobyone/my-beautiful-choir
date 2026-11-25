# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Observer of personal mode."""

from uuid import UUID

from my_beautiful_choir.authorization.observer import LOCAL_USER, Observer
from my_beautiful_choir.authorization.observer_source import ObserverSource


class LocalObserverSource(ObserverSource):
    """The implicit user of personal mode observes every choir and sees everything."""

    def observer(self, choir_id: UUID) -> Observer:
        """The local user."""
        return LOCAL_USER
