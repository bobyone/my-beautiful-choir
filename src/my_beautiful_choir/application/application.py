# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Orchestration of the application lifecycle."""

import logging
from collections.abc import Sequence

import anyio
from mcp.server.mcpserver import MCPServer

from my_beautiful_choir.application.application_info import ApplicationInfo
from my_beautiful_choir.application.startup_step import StartupStep
from my_beautiful_choir.mcp.mcp_server_builder import McpServerBuilder
from my_beautiful_choir.transport.transport import Transport

_LOGGER = logging.getLogger(__name__)


class Application:
    """Builds the MCP server, runs the startup steps, then serves with the transport of the mode."""

    def __init__(
        self,
        application_info: ApplicationInfo,
        server_builder: McpServerBuilder,
        transport: Transport,
        startup_steps: Sequence[StartupStep] = (),
    ) -> None:
        self._application_info = application_info
        self._server_builder = server_builder
        self._transport = transport
        self._startup_steps = startup_steps

    def run(self) -> None:
        """Serve until the transport stops.

        Raises:
            StartupError: if the server, a startup step or the transport cannot start.
        """
        info = self._application_info
        server = self._server_builder.build()
        _LOGGER.info(
            "Starting my-beautiful-choir", extra={"version": info.version, "mode": info.mode.value}
        )
        anyio.run(self._serve, server)
        _LOGGER.info("my-beautiful-choir stopped")

    async def _serve(self, server: MCPServer) -> None:
        for step in self._startup_steps:
            _LOGGER.info("Startup step", extra={"step": step.name})
            await step.run()
        await self._transport.run(server)
