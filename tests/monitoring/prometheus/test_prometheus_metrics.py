# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the Prometheus metrics."""

from my_beautiful_choir.monitoring.prometheus.prometheus_metrics import PrometheusMetrics


def test_tool_calls_are_counted_by_outcome() -> None:
    metrics = PrometheusMetrics()
    metrics.record_tool_call("show_about", 0.2, failed=False)
    metrics.record_tool_call("show_about", 0.3, failed=True)
    body = metrics.export().body.decode("utf-8")
    assert 'mbc_tool_calls_total{outcome="success",tool="show_about"} 1.0' in body
    assert 'mbc_tool_calls_total{outcome="error",tool="show_about"} 1.0' in body
    assert 'mbc_tool_call_duration_seconds_count{tool="show_about"} 2.0' in body


def test_http_requests_are_counted() -> None:
    metrics = PrometheusMetrics()
    metrics.record_http_request("GET", "/healthz", 200, 0.01)
    body = metrics.export().body.decode("utf-8")
    assert 'mbc_http_requests_total{method="GET",route="/healthz",status="200"} 1.0' in body
    assert 'mbc_http_request_duration_seconds_count{method="GET",route="/healthz"} 1.0' in body


def test_each_instance_has_its_own_registry() -> None:
    first = PrometheusMetrics()
    first.record_tool_call("show_about", 0.1, failed=False)
    assert b"show_about" not in PrometheusMetrics().export().body


def test_export_uses_prometheus_media_type() -> None:
    assert PrometheusMetrics().export().content_type.startswith("text/plain; version=")
