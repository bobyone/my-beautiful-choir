# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the null metrics."""

from my_beautiful_choir.monitoring.null_metrics import NullMetrics


def test_records_nothing_and_exports_empty_body() -> None:
    metrics = NullMetrics()
    metrics.record_tool_call("show_about", 0.1, failed=False)
    metrics.record_http_request("GET", "/healthz", 200, 0.01)
    export = metrics.export()
    assert export.body == b""
    assert export.content_type.startswith("text/plain")
