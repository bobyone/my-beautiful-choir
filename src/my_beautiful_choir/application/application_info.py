# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Information about the running application."""

from dataclasses import dataclass

from my_beautiful_choir.configuration.mode import Mode


@dataclass(frozen=True)
class ApplicationInfo:
    """Name, version and mode of the running application, fixed at startup."""

    name: str
    version: str
    mode: Mode
