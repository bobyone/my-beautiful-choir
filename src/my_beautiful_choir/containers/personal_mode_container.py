# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Assembly specific to personal mode."""

from typing import Any

from dependency_injector import containers, providers

from my_beautiful_choir.authorization.local.local_user_authorization import LocalUserAuthorization
from my_beautiful_choir.choirs.choir_service import ChoirService
from my_beautiful_choir.clock.system_clock import SystemClock
from my_beautiful_choir.configuration.settings import Settings
from my_beautiful_choir.monitoring.null_metrics import NullMetrics
from my_beautiful_choir.persistence.sql.prepare_data_store import PrepareDataStore
from my_beautiful_choir.persistence.sql.sql_database import SqlDatabase
from my_beautiful_choir.tools.choirs.create_choir_tool import CreateChoirTool
from my_beautiful_choir.tools.choirs.list_choirs_tool import ListChoirsTool
from my_beautiful_choir.tools.choirs.rename_choir_tool import RenameChoirTool
from my_beautiful_choir.tools.choirs.set_default_choir_tool import SetDefaultChoirTool
from my_beautiful_choir.tools.metered_tool import MeteredTool
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.transport.stdio.stdio_transport import StdioTransport


def _metered(
    tool: type[Tool[Any]], service: providers.Provider[Any], metrics: providers.Provider[Any]
) -> providers.Singleton[MeteredTool[Any]]:
    """Provider of ``tool``, built with ``service`` and wrapped to record its metrics."""
    return providers.Singleton(
        MeteredTool, inner=providers.Singleton(tool, service=service), metrics=metrics
    )


class PersonalModeContainer(containers.DeclarativeContainer):
    """Personal mode: stdio transport, no metrics, SQLite database in the data directory."""

    settings = providers.Dependency(instance_of=Settings)

    metrics = providers.Singleton(NullMetrics)
    transport = providers.Singleton(StdioTransport)

    data_dir = settings.provided.data_dir
    database = providers.Singleton(SqlDatabase.in_directory, data_dir=data_dir)
    startup_steps = providers.List(
        providers.Singleton(PrepareDataStore, data_dir=data_dir, database=database)
    )
    unit_of_work = database.provided.unit_of_work

    clock = providers.Singleton(SystemClock)
    authorization = providers.Singleton(LocalUserAuthorization)

    choir_service = providers.Singleton(
        ChoirService, unit_of_work=unit_of_work, clock=clock, authorization=authorization
    )

    mode_tools = providers.List(
        _metered(ListChoirsTool, choir_service, metrics),
        _metered(CreateChoirTool, choir_service, metrics),
        _metered(RenameChoirTool, choir_service, metrics),
        _metered(SetDefaultChoirTool, choir_service, metrics),
    )
