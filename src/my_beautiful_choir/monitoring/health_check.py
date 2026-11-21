# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Health check abstraction."""

from abc import ABC, abstractmethod

from my_beautiful_choir.monitoring.health_status import HealthStatus


class HealthCheck(ABC):
    """Tells whether the application can serve requests."""

    @abstractmethod
    def status(self) -> HealthStatus:
        """Return the current health status."""
