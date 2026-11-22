# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the application orchestrator."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from mcp.server.mcpserver import MCPServer

from my_beautiful_choir.application.application import Application
from my_beautiful_choir.application.application_info import ApplicationInfo
from my_beautiful_choir.application.startup_step import StartupStep
from my_beautiful_choir.configuration.mode import Mode
from my_beautiful_choir.mcp.mcp_server_builder import McpServerBuilder
from my_beautiful_choir.persistence.errors import DataStoreError
from my_beautiful_choir.transport.transport import Transport
from my_beautiful_choir.views.errors import ViewNotFoundError

INFO = ApplicationInfo("my-beautiful-choir", "1.2.3", Mode.PERSONAL)


class _RecordingTransport(Transport):
    def __init__(self, events: list[str] | None = None) -> None:
        self.served: list[MCPServer] = []
        self._events = events if events is not None else []

    async def run(self, server: MCPServer) -> None:
        self._events.append("serve")
        self.served.append(server)


class _Step(StartupStep):
    def __init__(self, step_name: str, events: list[str], fail: bool = False) -> None:
        self._name = step_name
        self._events = events
        self._fail = fail

    @property
    def name(self) -> str:
        return self._name

    async def run(self) -> None:
        self._events.append(self._name)
        if self._fail:
            raise DataStoreError(Path("data"), "not writable")


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


def test_startup_steps_run_in_order_before_serving() -> None:
    events: list[str] = []
    builder = MagicMock(spec=McpServerBuilder)
    builder.build.return_value = MCPServer("test")
    steps = [_Step("first", events), _Step("second", events)]
    Application(INFO, builder, _RecordingTransport(events), steps).run()
    assert events == ["first", "second", "serve"]


def test_failed_startup_step_prevents_serving() -> None:
    events: list[str] = []
    builder = MagicMock(spec=McpServerBuilder)
    builder.build.return_value = MCPServer("test")
    steps = [_Step("first", events, fail=True), _Step("second", events)]
    with pytest.raises(DataStoreError):
        Application(INFO, builder, _RecordingTransport(events), steps).run()
    assert events == ["first"]
