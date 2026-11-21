# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""ASGI middleware measuring and logging HTTP requests."""

import logging
import time
from collections.abc import Collection

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from my_beautiful_choir.monitoring.metrics import Metrics

_LOGGER = logging.getLogger(__name__)

OTHER_ROUTE = "other"


class MetricsMiddleware:
    """Records each HTTP request in the metrics and logs it, without the client address.

    Unknown paths are grouped under the ``other`` route, so that the number of
    metric series stays bounded.
    """

    def __init__(self, app: ASGIApp, metrics: Metrics, known_routes: Collection[str]) -> None:
        self._app = app
        self._metrics = metrics
        self._known_routes = frozenset(known_routes)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Measure the request, then record and log it."""
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        start = time.perf_counter()
        status_code = 500

        async def send_and_capture_status(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self._app(scope, receive, send_and_capture_status)
        finally:
            duration = time.perf_counter() - start
            path = scope["path"]
            route = path if path in self._known_routes else OTHER_ROUTE
            method = scope["method"]
            self._metrics.record_http_request(method, route, status_code, duration)
            _LOGGER.info(
                "HTTP request",
                extra={
                    "method": method,
                    "route": route,
                    "status": status_code,
                    "duration_seconds": round(duration, 6),
                },
            )
