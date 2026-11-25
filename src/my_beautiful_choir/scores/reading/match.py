# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Explicit matches between positions in two scores."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Match:
    """The two positions associated for a comparison."""

    before: int
    after: int
