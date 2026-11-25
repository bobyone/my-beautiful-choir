# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Scope tool calls to the lifetime of a personal stdio connection."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

connection_identity: ContextVar[object | None] = ContextVar("connection_identity", default=None)


@contextmanager
def stdio_connection_scope() -> Iterator[None]:
    """Bind one identity for every request on this stdio connection."""
    token = connection_identity.set(object())
    try:
        yield
    finally:
        connection_identity.reset(token)
