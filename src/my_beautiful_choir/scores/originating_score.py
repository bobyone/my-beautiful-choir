# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Lineage retained even when the originating score is deleted."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class OriginatingScore:
    """The final score from which a draft was duplicated."""

    id: UUID
    label: str
    version_number: int
