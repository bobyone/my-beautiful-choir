# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Assembly specific to web mode."""

from dependency_injector import containers, providers

from my_beautiful_choir.configuration.settings import Settings
from my_beautiful_choir.monitoring.prometheus.prometheus_metrics import PrometheusMetrics
from my_beautiful_choir.monitoring.server.server_health_check import ServerHealthCheck
from my_beautiful_choir.transport.http.http_transport import HttpTransport


class WebModeContainer(containers.DeclarativeContainer):
    """Web mode: Streamable HTTP transport, Prometheus metrics, health check."""

    settings = providers.Dependency(instance_of=Settings)

    metrics = providers.Singleton(PrometheusMetrics)
    health_check = providers.Singleton(ServerHealthCheck)
    transport = providers.Singleton(
        HttpTransport,
        settings=settings.provided.web,
        metrics=metrics,
        health_check=health_check,
    )
