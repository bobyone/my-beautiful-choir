# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Choir value object."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Choir:
    """A group of people singing together; the unit whose data is isolated."""

    id: UUID
    name: str
    """Name, unique among the user's choirs, ignoring case."""
    created_at: datetime
    is_default: bool
    """True for the choir used when a request names none."""
