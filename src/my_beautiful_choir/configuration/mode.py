# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Running mode of the application."""

from enum import StrEnum


class Mode(StrEnum):
    """Running mode: personal mode over stdio, or web mode over HTTP."""

    PERSONAL = "personal"
    WEB = "web"
