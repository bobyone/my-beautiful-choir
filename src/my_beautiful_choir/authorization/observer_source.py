# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Observer source abstraction."""

from abc import ABC, abstractmethod
from uuid import UUID

from my_beautiful_choir.authorization.observer import Observer


class ObserverSource(ABC):
    """Tells who is consulting the events of a choir (ADR 0031)."""

    @abstractmethod
    def observer(self, choir_id: UUID) -> Observer:
        """The current observer for the choir ``choir_id``."""
