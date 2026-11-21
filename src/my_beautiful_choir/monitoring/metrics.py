# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Metrics abstraction."""

from abc import ABC, abstractmethod

from my_beautiful_choir.monitoring.metrics_export import MetricsExport


class Metrics(ABC):
    """Records the activity of the application: tool calls and HTTP requests."""

    @abstractmethod
    def record_tool_call(self, tool_name: str, duration_seconds: float, failed: bool) -> None:
        """Record one call of an MCP tool."""

    @abstractmethod
    def record_http_request(
        self, method: str, route: str, status_code: int, duration_seconds: float
    ) -> None:
        """Record one HTTP request; ``route`` is the route template, never the raw path."""

    @abstractmethod
    def export(self) -> MetricsExport:
        """Serialize the recorded metrics."""
