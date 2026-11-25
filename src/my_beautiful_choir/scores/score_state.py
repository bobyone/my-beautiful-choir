# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Whether a score can still be edited."""

from enum import StrEnum


class ScoreState(StrEnum):
    """Stored lifecycle state of a score."""

    DRAFT = "draft"
    FINAL = "final"
