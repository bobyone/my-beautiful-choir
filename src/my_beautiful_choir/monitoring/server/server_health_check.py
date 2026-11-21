# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Health check following the lifecycle of the server."""

from my_beautiful_choir.monitoring.health_check import HealthCheck
from my_beautiful_choir.monitoring.health_status import HealthStatus


class ServerHealthCheck(HealthCheck):
    """Unavailable until the server listens, ready while it serves, unavailable when stopping."""

    def __init__(self) -> None:
        self._status = HealthStatus.UNAVAILABLE

    def mark_ready(self) -> None:
        """Called once the server listens."""
        self._status = HealthStatus.READY

    def mark_unavailable(self) -> None:
        """Called when the server starts shutting down."""
        self._status = HealthStatus.UNAVAILABLE

    def status(self) -> HealthStatus:
        """Return the current status."""
        return self._status
