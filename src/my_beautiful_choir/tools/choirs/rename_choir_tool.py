# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool renaming a choir."""

from pydantic import BaseModel, Field

from my_beautiful_choir.choirs.choir_name import MAXIMUM_LENGTH
from my_beautiful_choir.choirs.choir_service import ChoirService
from my_beautiful_choir.tools.choirs.choir_data import choir_data
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class RenameChoirArguments(BaseModel):
    """Arguments of ``rename_choir``."""

    choir: str = Field(description="Current name of the choir, ignoring case.")
    new_name: str = Field(description=f"New name, unique, at most {MAXIMUM_LENGTH} characters.")


class RenameChoirTool(Tool[RenameChoirArguments]):
    """Renames a choir."""

    def __init__(self, service: ChoirService) -> None:
        self._service = service

    @property
    def name(self) -> str:
        """``rename_choir``."""
        return "rename_choir"

    @property
    def description(self) -> str:
        """Description for the model."""
        return "Rename a choir."

    @property
    def arguments_model(self) -> type[RenameChoirArguments]:
        """The current and new names."""
        return RenameChoirArguments

    async def execute(self, arguments: RenameChoirArguments, context: ToolContext) -> ToolResult:
        """Rename the choir."""
        choir = await self._service.rename(arguments.choir, arguments.new_name)
        return ToolResult(
            text=f"The choir is now named {choir.name}.",
            structured={"choir": choir_data(choir)},
        )
