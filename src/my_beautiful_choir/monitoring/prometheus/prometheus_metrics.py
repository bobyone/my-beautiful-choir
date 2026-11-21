# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Metrics exposed in the Prometheus text format."""

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Histogram
from prometheus_client.exposition import generate_latest

from my_beautiful_choir.monitoring.metrics import Metrics
from my_beautiful_choir.monitoring.metrics_export import MetricsExport


class PrometheusMetrics(Metrics):
    """Counts and times tool calls and HTTP requests in a dedicated Prometheus registry.

    Exposed series:

    - ``mbc_tool_calls_total{tool, outcome}`` and ``mbc_tool_call_duration_seconds{tool}``;
    - ``mbc_http_requests_total{method, route, status}`` and
      ``mbc_http_request_duration_seconds{method, route}``.
    """

    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        self._registry = registry if registry is not None else CollectorRegistry()
        self._tool_calls = Counter(
            "mbc_tool_calls",
            "MCP tool calls, by tool and outcome.",
            ["tool", "outcome"],
            registry=self._registry,
        )
        self._tool_durations = Histogram(
            "mbc_tool_call_duration_seconds",
            "Duration of MCP tool calls, by tool.",
            ["tool"],
            registry=self._registry,
        )
        self._http_requests = Counter(
            "mbc_http_requests",
            "HTTP requests, by method, route and status code.",
            ["method", "route", "status"],
            registry=self._registry,
        )
        self._http_durations = Histogram(
            "mbc_http_request_duration_seconds",
            "Duration of HTTP requests, by method and route.",
            ["method", "route"],
            registry=self._registry,
        )

    def record_tool_call(self, tool_name: str, duration_seconds: float, failed: bool) -> None:
        """Count the call and observe its duration."""
        outcome = "error" if failed else "success"
        self._tool_calls.labels(tool=tool_name, outcome=outcome).inc()
        self._tool_durations.labels(tool=tool_name).observe(duration_seconds)

    def record_http_request(
        self, method: str, route: str, status_code: int, duration_seconds: float
    ) -> None:
        """Count the request and observe its duration."""
        self._http_requests.labels(method=method, route=route, status=str(status_code)).inc()
        self._http_durations.labels(method=method, route=route).observe(duration_seconds)

    def export(self) -> MetricsExport:
        """Serialize the registry in the Prometheus text format."""
        return MetricsExport(content_type=CONTENT_TYPE_LATEST, body=generate_latest(self._registry))
