# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Authorization of the implicit user of personal mode."""

from uuid import UUID

from my_beautiful_choir.authorization.authorization import Authorization
from my_beautiful_choir.authorization.permission import Permission


class LocalUserAuthorization(Authorization):
    """The implicit user of personal mode manages every choir: everything is allowed."""

    def require(self, permission: Permission, choir_id: UUID | None = None) -> None:
        """Allow every permission."""
