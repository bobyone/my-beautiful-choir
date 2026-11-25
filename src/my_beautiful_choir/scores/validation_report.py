# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Results of validating a draft score."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationReport:
    """Errors that prevent finalisation."""

    errors: tuple[str, ...] = ()
