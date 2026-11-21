# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the server health check."""

from my_beautiful_choir.monitoring.health_status import HealthStatus
from my_beautiful_choir.monitoring.server.server_health_check import ServerHealthCheck


def test_follows_the_server_lifecycle() -> None:
    health = ServerHealthCheck()
    assert health.status() is HealthStatus.UNAVAILABLE
    health.mark_ready()
    assert health.status() is HealthStatus.READY
    health.mark_unavailable()
    assert health.status() is HealthStatus.UNAVAILABLE
