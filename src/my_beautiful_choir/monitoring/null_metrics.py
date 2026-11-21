# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Metrics that record nothing (Null Object), used in personal mode."""

from my_beautiful_choir.monitoring.metrics import Metrics
from my_beautiful_choir.monitoring.metrics_export import MetricsExport


class NullMetrics(Metrics):
    """Ignores every measure; its export is empty."""

    def record_tool_call(self, tool_name: str, duration_seconds: float, failed: bool) -> None:
        """Ignore the tool call."""

    def record_http_request(
        self, method: str, route: str, status_code: int, duration_seconds: float
    ) -> None:
        """Ignore the HTTP request."""

    def export(self) -> MetricsExport:
        """Return an empty plain text export."""
        return MetricsExport(content_type="text/plain; charset=utf-8", body=b"")
