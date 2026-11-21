# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Assembly shared by every mode."""

from dependency_injector import containers, providers

from my_beautiful_choir import APPLICATION_NAME, __version__
from my_beautiful_choir.application.application import Application
from my_beautiful_choir.application.application_info import ApplicationInfo
from my_beautiful_choir.configuration.settings import Settings
from my_beautiful_choir.mcp.mcp_server_builder import McpServerBuilder
from my_beautiful_choir.tools.metered_tool import MeteredTool
from my_beautiful_choir.tools.view_tool.about.show_about_tool import ShowAboutTool
from my_beautiful_choir.views.packaged.packaged_view import PackagedView, packaged_views_directory


class ApplicationContainer(containers.DeclarativeContainer):
    """Providers common to both modes.

    The mode-specific providers (``metrics``, ``transport``, ``startup_steps``) come from the
    injected ``mode`` container: ``PersonalModeContainer`` or ``WebModeContainer``.
    """

    settings = providers.Dependency(instance_of=Settings)
    mode = providers.DependenciesContainer()

    application_info = providers.Singleton(
        ApplicationInfo, name=APPLICATION_NAME, version=__version__, mode=settings.provided.mode
    )

    views_directory = providers.Callable(packaged_views_directory)
    about_view = providers.Singleton(PackagedView, name="about", directory=views_directory)

    show_about_tool = providers.Singleton(
        MeteredTool,
        inner=providers.Singleton(
            ShowAboutTool, view=about_view, application_info=application_info
        ),
        metrics=mode.metrics,
    )
    tools = providers.List(show_about_tool)

    server_builder = providers.Singleton(
        McpServerBuilder, application_info=application_info, tools=tools
    )
    application = providers.Singleton(
        Application,
        application_info=application_info,
        server_builder=server_builder,
        transport=mode.transport,
        startup_steps=mode.startup_steps,
    )
