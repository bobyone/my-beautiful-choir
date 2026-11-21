# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Orchestration of the application lifecycle."""

import logging

import anyio

from my_beautiful_choir.application.application_info import ApplicationInfo
from my_beautiful_choir.mcp.mcp_server_builder import McpServerBuilder
from my_beautiful_choir.transport.transport import Transport

_LOGGER = logging.getLogger(__name__)


class Application:
    """Builds the MCP server, then serves it with the transport of the current mode."""

    def __init__(
        self,
        application_info: ApplicationInfo,
        server_builder: McpServerBuilder,
        transport: Transport,
    ) -> None:
        self._application_info = application_info
        self._server_builder = server_builder
        self._transport = transport

    def run(self) -> None:
        """Serve until the transport stops.

        Raises:
            StartupError: if the server or the transport cannot start.
        """
        info = self._application_info
        server = self._server_builder.build()
        _LOGGER.info(
            "Starting my-beautiful-choir", extra={"version": info.version, "mode": info.mode.value}
        )
        anyio.run(self._transport.run, server)
        _LOGGER.info("my-beautiful-choir stopped")
