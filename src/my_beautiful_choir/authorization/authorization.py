# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Authorization abstraction."""

from abc import ABC, abstractmethod
from uuid import UUID

from my_beautiful_choir.authorization.permission import Permission


class Authorization(ABC):
    """Checks the rights of the current user (ADR 0003)."""

    @abstractmethod
    def require(self, permission: Permission, choir_id: UUID | None = None) -> None:
        """Check that the current user has ``permission``, in ``choir_id`` when given.

        Raises:
            AccessDeniedError: if the user does not have the permission.
        """
