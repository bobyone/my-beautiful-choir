# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Permissions checked by the authorization."""

from enum import StrEnum


class Permission(StrEnum):
    """An action that requires a right."""

    MANAGE_CHOIRS = "manage_choirs"
    """Create, rename and delete choirs, and choose the default choir."""

    MANAGE_REPERTOIRE = "manage_repertoire"
    """Add, edit and delete the works and scores of a choir (manager)."""

    CONSULT_REPERTOIRE = "consult_repertoire"
    """Consult the repertoire of a choir and open its scores (manager or chorister)."""
