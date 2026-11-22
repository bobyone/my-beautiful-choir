# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool showing information about the running application."""

from collections.abc import Mapping

from my_beautiful_choir.application.application_info import ApplicationInfo
from my_beautiful_choir.tools.no_arguments import NoArguments
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.view_tool.view_tool import ViewTool
from my_beautiful_choir.views.view import View


class ShowAboutTool(ViewTool[NoArguments]):
    """Shows the name, version and mode of my-beautiful-choir."""

    def __init__(self, view: View, application_info: ApplicationInfo) -> None:
        super().__init__(view)
        self._application_info = application_info

    @property
    def name(self) -> str:
        """``show_about``."""
        return "show_about"

    @property
    def description(self) -> str:
        """Description for the model."""
        return (
            "Show information about my-beautiful-choir, the choir management application: "
            "its version and its running mode (personal mode or web mode)."
        )

    @property
    def arguments_model(self) -> type[NoArguments]:
        """No argument."""
        return NoArguments

    async def _collect(self, arguments: NoArguments, context: ToolContext) -> Mapping[str, object]:
        info = self._application_info
        return {"name": info.name, "version": info.version, "mode": info.mode.value}

    def _describe(self, data: Mapping[str, object]) -> str:
        return f"{data['name']} {data['version']}, {data['mode']} mode."
