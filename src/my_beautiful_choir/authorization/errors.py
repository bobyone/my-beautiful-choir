# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Exceptions of the authorization notion."""

from my_beautiful_choir.errors import DomainError


class AccessDeniedError(DomainError):
    """The current user does not have the permission required by the operation."""
