# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Streamable HTTP transport."""

import logging
import os
import socket

import uvicorn
from asgi_correlation_id import CorrelationIdMiddleware
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.types import ASGIApp

from my_beautiful_choir.configuration.web_settings import WebSettings
from my_beautiful_choir.monitoring.metrics import Metrics
from my_beautiful_choir.monitoring.server.server_health_check import ServerHealthCheck
from my_beautiful_choir.transport.errors import PortUnavailableError
from my_beautiful_choir.transport.http.metrics_middleware import MetricsMiddleware
from my_beautiful_choir.transport.http.monitoring_routes import (
    HEALTH_PATH,
    METRICS_PATH,
    add_monitoring_routes,
)
from my_beautiful_choir.transport.transport import Transport

_LOGGER = logging.getLogger(__name__)

MCP_PATH = "/mcp"
CORRELATION_HEADER = "X-Request-ID"
LOCAL_HOSTS = ("127.0.0.1:*", "localhost:*", "[::1]:*")


def transport_security_for(settings: WebSettings) -> TransportSecuritySettings:
    """DNS rebinding protection: local hosts are always allowed, plus the configured ones."""
    hosts = [*LOCAL_HOSTS, *settings.allowed_hosts]
    origins = [f"{scheme}://{host}" for host in hosts for scheme in ("http", "https")]
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True, allowed_hosts=hosts, allowed_origins=origins
    )


class _LifecycleServer(uvicorn.Server):
    """Uvicorn server reporting its lifecycle to the health check."""

    def __init__(self, config: uvicorn.Config, health_check: ServerHealthCheck) -> None:
        super().__init__(config)
        self._health_check = health_check

    async def startup(self, sockets: list[socket.socket] | None = None) -> None:
        await super().startup(sockets)
        if self.started:
            self._health_check.mark_ready()

    async def shutdown(self, sockets: list[socket.socket] | None = None) -> None:
        self._health_check.mark_unavailable()
        await super().shutdown(sockets)


class HttpTransport(Transport):
    """Serves MCP over Streamable HTTP on ``/mcp``, with ``/healthz`` and ``/metrics``.

    Each request gets a correlation id (``X-Request-ID``, reused when valid),
    is recorded in the metrics and logged without the client address.
    """

    def __init__(
        self, settings: WebSettings, metrics: Metrics, health_check: ServerHealthCheck
    ) -> None:
        self._settings = settings
        self._metrics = metrics
        self._health_check = health_check
        self._server: _LifecycleServer | None = None

    def request_stop(self) -> None:
        """Ask the running server to stop gracefully, as a stop signal would."""
        if self._server is not None:
            self._server.should_exit = True

    def create_app(self, server: MCPServer) -> ASGIApp:
        """Return the ASGI application serving ``server`` and the monitoring routes."""
        add_monitoring_routes(server, self._health_check, self._metrics)
        app = server.streamable_http_app(
            streamable_http_path=MCP_PATH,
            host=self._settings.host,
            transport_security=transport_security_for(self._settings),
        )
        measured = MetricsMiddleware(app, self._metrics, (MCP_PATH, HEALTH_PATH, METRICS_PATH))
        return CorrelationIdMiddleware(measured, header_name=CORRELATION_HEADER)

    def bind(self) -> socket.socket:
        """Open the listening socket.

        Raises:
            PortUnavailableError: if the address cannot be listened on.
        """
        host, port = self._settings.host, self._settings.port
        try:
            address = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)[0]
            listener = socket.socket(address[0], socket.SOCK_STREAM)
            if os.name != "nt":
                # On Windows, SO_REUSEADDR would allow binding a port already in use.
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(address[4])
        except OSError as error:
            raise PortUnavailableError(host, port, error.strerror or str(error)) from error
        listener.set_inheritable(True)
        return listener

    async def run(self, server: MCPServer) -> None:
        """Serve until a stop signal is received; in-flight requests are completed."""
        listener = self.bind()
        config = uvicorn.Config(
            self.create_app(server), log_config=None, access_log=False, lifespan="on"
        )
        _LOGGER.info(
            "Serving MCP over HTTP",
            extra={"host": self._settings.host, "port": self._settings.port, "path": MCP_PATH},
        )
        self._server = _LifecycleServer(config, self._health_check)
        try:
            await self._server.serve(sockets=[listener])
        finally:
            self._server = None
            listener.close()
            _LOGGER.info("HTTP server stopped")
