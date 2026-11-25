# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Observer value object."""

from dataclasses import dataclass
from uuid import UUID

from my_beautiful_choir.authorization.observer_kind import ObserverKind


@dataclass(frozen=True)
class Observer:
    """Person consulting the events of one choir."""

    kind: ObserverKind
    member_id: UUID | None = None
    """Member of the choir, for a manager or a chorister."""


LOCAL_USER = Observer(ObserverKind.LOCAL_USER)
"""The implicit user of personal mode."""

PUBLIC = Observer(ObserverKind.PUBLIC)
"""Someone who is not a member of the choir."""
