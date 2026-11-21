# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the entry point and its exit codes."""

import logging
import socket
from collections.abc import Iterator
from pathlib import Path

import pytest
from dependency_injector import providers
from mcp.server.mcpserver import MCPServer

from my_beautiful_choir import cli
from my_beautiful_choir.configuration.settings import Settings
from my_beautiful_choir.containers import container_factory
from my_beautiful_choir.containers.application_container import ApplicationContainer
from my_beautiful_choir.transport.transport import Transport


class _ScriptedTransport(Transport):
    def __init__(self, error: BaseException | None = None) -> None:
        self.error = error
        self.served = False

    async def run(self, server: MCPServer) -> None:
        self.served = True
        if self.error is not None:
            raise self.error


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for key in ("MBC_MODE", "MBC_LOG_LEVEL", "MBC_WEB__HOST", "MBC_WEB__PORT"):
        monkeypatch.delenv(key, raising=False)
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    yield
    root.handlers[:] = handlers
    root.setLevel(level)
    logging.getLogger("uvicorn.access").disabled = False


@pytest.fixture
def views(tmp_path: Path) -> Path:
    (tmp_path / "about.html").write_text("<p>about</p>", encoding="utf-8")
    return tmp_path


def _use(monkeypatch: pytest.MonkeyPatch, views: Path, transport: Transport | None = None) -> None:
    """Assemble the real containers, with test views and, optionally, a scripted transport."""
    create_container = container_factory.create_container

    def create_test_container(settings: Settings) -> ApplicationContainer:
        container = create_container(settings)
        container.views_directory.override(providers.Object(views))
        if transport is not None:
            container.mode.transport.override(providers.Object(transport))
        return container

    monkeypatch.setattr(container_factory, "create_container", create_test_container)


def test_normal_stop_exits_with_0(monkeypatch: pytest.MonkeyPatch, views: Path) -> None:
    transport = _ScriptedTransport()
    _use(monkeypatch, views, transport)
    assert cli.main([]) == 0
    assert transport.served


def test_invalid_command_line_exits_with_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["--mode", "cloud"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "could not start [MBC-CONFIG]: invalid configuration." in captured.err
    assert "troubleshoot-startup.md" in captured.err


def test_invalid_environment_exits_with_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("MBC_WEB__PORT", "90000")
    assert cli.main([]) == 2
    err = capsys.readouterr().err
    assert "  - MBC_WEB__PORT: '90000' is not valid" in err
    assert '"startup_failed"' in err
    assert '"error_code": "MBC-CONFIG"' in err


def test_port_in_use_exits_with_3(
    monkeypatch: pytest.MonkeyPatch, views: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _use(monkeypatch, views)
    with socket.socket() as occupant:
        occupant.bind(("127.0.0.1", 0))
        occupant.listen()
        monkeypatch.setenv("MBC_WEB__PORT", str(occupant.getsockname()[1]))
        assert cli.main(["--mode", "web"]) == 3
    assert "[MBC-PORT]" in capsys.readouterr().err


def test_missing_view_exits_with_4(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _use(monkeypatch, tmp_path, _ScriptedTransport())
    assert cli.main([]) == 4
    err = capsys.readouterr().err
    assert "[MBC-INSTALL]" in err
    assert "ui://my-beautiful-choir/about.html" in err


def test_unexpected_error_exits_with_1(
    monkeypatch: pytest.MonkeyPatch, views: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _use(monkeypatch, views, _ScriptedTransport(RuntimeError("secret detail")))
    assert cli.main([]) == 1
    err = capsys.readouterr().err
    assert "could not start [MBC-UNEXPECTED]" in err
    assert '"exc_info"' in err


def test_interruption_exits_with_0(monkeypatch: pytest.MonkeyPatch, views: Path) -> None:
    _use(monkeypatch, views, _ScriptedTransport(KeyboardInterrupt()))
    assert cli.main([]) == 0


def test_log_level_comes_from_the_settings(monkeypatch: pytest.MonkeyPatch, views: Path) -> None:
    monkeypatch.setenv("MBC_LOG_LEVEL", "WARNING")
    _use(monkeypatch, views, _ScriptedTransport())
    cli.main([])
    assert logging.getLogger().level == logging.WARNING
