# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Transport abstraction."""

from abc import ABC, abstractmethod

from mcp.server.mcpserver import MCPServer


class Transport(ABC):
    """Carries MCP messages between the client and the server, until shutdown."""

    @abstractmethod
    async def run(self, server: MCPServer) -> None:
        """Serve ``server`` until the client disconnects or a stop signal is received.

        Raises:
            StartupError: if the transport cannot start.
        """
