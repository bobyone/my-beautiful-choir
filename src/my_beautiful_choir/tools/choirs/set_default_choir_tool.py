# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool choosing the default choir."""

from pydantic import BaseModel, Field

from my_beautiful_choir.choirs.choir_service import ChoirService
from my_beautiful_choir.tools.choirs.choir_data import choir_data
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class SetDefaultChoirArguments(BaseModel):
    """Arguments of ``set_default_choir``."""

    choir: str = Field(description="Name of the choir to use by default, ignoring case.")


class SetDefaultChoirTool(Tool[SetDefaultChoirArguments]):
    """Chooses the default choir."""

    def __init__(self, service: ChoirService) -> None:
        self._service = service

    @property
    def name(self) -> str:
        """``set_default_choir``."""
        return "set_default_choir"

    @property
    def description(self) -> str:
        """Description for the model."""
        return "Choose the default choir, used when a request names no choir."

    @property
    def arguments_model(self) -> type[SetDefaultChoirArguments]:
        """The choir."""
        return SetDefaultChoirArguments

    async def execute(
        self, arguments: SetDefaultChoirArguments, context: ToolContext
    ) -> ToolResult:
        """Make the choir the default one."""
        choir = await self._service.set_default(arguments.choir)
        return ToolResult(
            text=f"{choir.name} is now the default choir.",
            structured={"choir": choir_data(choir)},
        )
