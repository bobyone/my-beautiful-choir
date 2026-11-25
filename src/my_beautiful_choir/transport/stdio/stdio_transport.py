# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Transport over standard input and output."""

import logging

from mcp.server.mcpserver import MCPServer

from my_beautiful_choir.mcp.connection_scope import stdio_connection_scope
from my_beautiful_choir.transport.transport import Transport

_LOGGER = logging.getLogger(__name__)


class StdioTransport(Transport):
    """Exchanges MCP messages on stdin and stdout, until stdin is closed.

    stdout is reserved to the protocol: logs go to stderr.
    """

    async def run(self, server: MCPServer) -> None:
        """Serve until the client closes stdin."""
        _LOGGER.info("Serving MCP over stdio")
        with stdio_connection_scope():
            await server.run_stdio_async()
        _LOGGER.info("Standard input closed, stopping")
