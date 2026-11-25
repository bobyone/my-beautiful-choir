# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Kinds of observers."""

from enum import StrEnum


class ObserverKind(StrEnum):
    """Who is consulting the events of a choir."""

    LOCAL_USER = "local_user"
    """The implicit user of personal mode, who sees everything."""

    INSTANCE_ADMINISTRATOR = "instance_administrator"
    """The administrator of a web mode instance."""

    MANAGER = "manager"
    """A member of the choir with the manager role."""

    CHORISTER = "chorister"
    """A member of the choir with the chorister role."""

    PUBLIC = "public"
    """Someone who is not a member of the choir."""
