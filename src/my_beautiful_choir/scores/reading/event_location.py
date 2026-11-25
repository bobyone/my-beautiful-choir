# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Location of a musical event within a part."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EventLocation:
    """A measure position and a 1-based event position within it."""

    measure: int
    event: int
