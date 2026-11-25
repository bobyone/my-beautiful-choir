# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Programme entry value object."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ProgrammeEntry:
    """Position in a programme that refers to a work, or to none, with an optional note."""

    position: int
    """Position in the programme, from 1."""
    work_id: UUID | None = None
    """Work of the choir's repertoire; None for an entry without a work or a deleted work."""
    work_title: str | None = None
    """Title of the work: the current one while the work exists, then the kept one."""
    note: str | None = None
