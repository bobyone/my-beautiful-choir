# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Health check and metrics HTTP routes."""

from mcp.server.mcpserver import MCPServer
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from my_beautiful_choir.monitoring.health_check import HealthCheck
from my_beautiful_choir.monitoring.health_status import HealthStatus
from my_beautiful_choir.monitoring.metrics import Metrics

HEALTH_PATH = "/healthz"
METRICS_PATH = "/metrics"


def add_monitoring_routes(server: MCPServer, health_check: HealthCheck, metrics: Metrics) -> None:
    """Add ``/healthz`` (200 when ready, 503 otherwise) and ``/metrics`` to the server."""

    async def health(request: Request) -> Response:
        status = health_check.status()
        code = 200 if status is HealthStatus.READY else 503
        return JSONResponse({"status": status.value}, status_code=code)

    async def export_metrics(request: Request) -> Response:
        export = metrics.export()
        return Response(export.body, media_type=export.content_type)

    server.custom_route(HEALTH_PATH, methods=["GET"], include_in_schema=False)(health)
    server.custom_route(METRICS_PATH, methods=["GET"], include_in_schema=False)(export_metrics)
