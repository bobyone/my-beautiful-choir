# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Assembly specific to personal mode."""

from dependency_injector import containers, providers

from my_beautiful_choir.configuration.settings import Settings
from my_beautiful_choir.monitoring.null_metrics import NullMetrics
from my_beautiful_choir.transport.stdio.stdio_transport import StdioTransport


class PersonalModeContainer(containers.DeclarativeContainer):
    """Personal mode: stdio transport, no metrics."""

    settings = providers.Dependency(instance_of=Settings)

    metrics = providers.Singleton(NullMetrics)
    transport = providers.Singleton(StdioTransport)
