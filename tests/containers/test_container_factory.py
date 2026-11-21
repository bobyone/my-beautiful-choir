# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the dependency assembly of each mode."""

from pathlib import Path

from dependency_injector import providers

from my_beautiful_choir import __version__
from my_beautiful_choir.application.application import Application
from my_beautiful_choir.configuration.mode import Mode
from my_beautiful_choir.configuration.settings import Settings
from my_beautiful_choir.configuration.web_settings import WebSettings
from my_beautiful_choir.containers.container_factory import create_container
from my_beautiful_choir.monitoring.null_metrics import NullMetrics
from my_beautiful_choir.monitoring.prometheus.prometheus_metrics import PrometheusMetrics
from my_beautiful_choir.monitoring.server.server_health_check import ServerHealthCheck
from my_beautiful_choir.persistence.sql.prepare_data_store import PrepareDataStore
from my_beautiful_choir.persistence.sql.sql_database import SqlDatabase
from my_beautiful_choir.tools.metered_tool import MeteredTool
from my_beautiful_choir.transport.http.http_transport import HttpTransport
from my_beautiful_choir.transport.stdio.stdio_transport import StdioTransport


def test_personal_mode_assembly() -> None:
    container = create_container(Settings(mode=Mode.PERSONAL))
    assert isinstance(container.application(), Application)
    assert isinstance(container.mode.transport(), StdioTransport)
    assert isinstance(container.mode.metrics(), NullMetrics)
    info = container.application_info()
    assert (info.name, info.version, info.mode) == (
        "my-beautiful-choir",
        __version__,
        Mode.PERSONAL,
    )


def test_web_mode_assembly_uses_the_web_settings() -> None:
    container = create_container(Settings(mode=Mode.WEB, web=WebSettings(port=1234)))
    transport = container.mode.transport()
    assert isinstance(transport, HttpTransport)
    assert transport.address == ("127.0.0.1", 1234)
    assert isinstance(container.mode.metrics(), PrometheusMetrics)
    assert isinstance(container.mode.health_check(), ServerHealthCheck)
    assert container.application_info().mode is Mode.WEB


def test_tools_are_metered_with_the_mode_metrics() -> None:
    container = create_container(Settings(mode=Mode.WEB))
    [tool] = container.tools()
    assert isinstance(tool, MeteredTool)
    assert tool.name == "show_about"
    assert container.mode.metrics() is container.mode.metrics()


def test_singletons_are_shared_within_a_container() -> None:
    container = create_container(Settings())
    assert container.application() is container.application()


def test_overrides_stay_within_their_container() -> None:
    overridden = create_container(Settings())
    overridden.mode.transport.override(providers.Object("fake"))
    assert overridden.mode.transport() == "fake"
    assert isinstance(create_container(Settings()).mode.transport(), StdioTransport)


def test_personal_mode_prepares_its_data_store(tmp_path: Path) -> None:
    container = create_container(Settings(mode=Mode.PERSONAL, data_dir=tmp_path))
    [step] = container.mode.startup_steps()
    assert isinstance(step, PrepareDataStore)
    database = container.mode.database()
    assert isinstance(database, SqlDatabase)
    assert database.engine.url.database == str(tmp_path / "my-beautiful-choir.sqlite3")
    assert container.mode.database() is database


def test_web_mode_has_no_startup_step() -> None:
    assert list(create_container(Settings(mode=Mode.WEB)).mode.startup_steps()) == []


def test_personal_mode_offers_the_choir_tools(tmp_path: Path) -> None:
    container = create_container(Settings(mode=Mode.PERSONAL, data_dir=tmp_path))
    names = [tool.name for tool in container.tools()]
    assert names == [
        "show_about",
        "list_choirs",
        "create_choir",
        "rename_choir",
        "set_default_choir",
        "add_work",
        "edit_work",
    ]
    assert all(isinstance(tool, MeteredTool) for tool in container.tools())


def test_web_mode_offers_no_repertoire_tool() -> None:
    container = create_container(Settings(mode=Mode.WEB))
    assert [tool.name for tool in container.tools()] == ["show_about"]
