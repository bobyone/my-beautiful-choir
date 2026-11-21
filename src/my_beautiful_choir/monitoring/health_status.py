# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Health status of the application."""

from enum import StrEnum


class HealthStatus(StrEnum):
    """Whether the application can serve requests."""

    READY = "ready"
    UNAVAILABLE = "unavailable"
