# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the application orchestrator."""

from unittest.mock import MagicMock

import pytest
from mcp.server.mcpserver import MCPServer

from my_beautiful_choir.application.application import Application
from my_beautiful_choir.application.application_info import ApplicationInfo
from my_beautiful_choir.configuration.mode import Mode
from my_beautiful_choir.mcp.mcp_server_builder import McpServerBuilder
from my_beautiful_choir.transport.transport import Transport
from my_beautiful_choir.views.errors import ViewNotFoundError

INFO = ApplicationInfo("my-beautiful-choir", "1.2.3", Mode.PERSONAL)


class _RecordingTransport(Transport):
    def __init__(self) -> None:
        self.served: list[MCPServer] = []

    async def run(self, server: MCPServer) -> None:
        self.served.append(server)


def test_builds_the_server_then_runs_the_transport() -> None:
    server = MCPServer("test")
    builder = MagicMock(spec=McpServerBuilder)
    builder.build.return_value = server
    transport = _RecordingTransport()
    Application(INFO, builder, transport).run()
    assert transport.served == [server]


def test_build_failure_prevents_serving() -> None:
    builder = MagicMock(spec=McpServerBuilder)
    builder.build.side_effect = ViewNotFoundError("ui://my-beautiful-choir/about.html")
    transport = _RecordingTransport()
    with pytest.raises(ViewNotFoundError):
        Application(INFO, builder, transport).run()
    assert transport.served == []
