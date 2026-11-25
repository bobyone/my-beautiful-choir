# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Programme item value object."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ProgrammeItem:
    """A programme entry as requested: a work of the repertoire, a note, or both."""

    work_id: UUID | None = None
    note: str | None = None
