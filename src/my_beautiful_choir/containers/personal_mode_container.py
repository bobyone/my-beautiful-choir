# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Assembly specific to personal mode."""

from dependency_injector import containers, providers

from my_beautiful_choir.configuration.settings import Settings
from my_beautiful_choir.monitoring.null_metrics import NullMetrics
from my_beautiful_choir.persistence.sql.prepare_data_store import PrepareDataStore
from my_beautiful_choir.persistence.sql.sql_database import SqlDatabase
from my_beautiful_choir.transport.stdio.stdio_transport import StdioTransport


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
