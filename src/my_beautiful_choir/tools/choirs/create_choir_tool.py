# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool creating a choir."""

from pydantic import BaseModel, Field

from my_beautiful_choir.choirs.choir_name import MAXIMUM_LENGTH
from my_beautiful_choir.choirs.choir_service import ChoirService
from my_beautiful_choir.tools.choirs.choir_data import choir_data
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class CreateChoirArguments(BaseModel):
    """Arguments of ``create_choir``."""

    name: str = Field(
        description=f"Name of the new choir, unique, at most {MAXIMUM_LENGTH} characters."
    )


class CreateChoirTool(Tool[CreateChoirArguments]):
    """Creates a choir."""

    def __init__(self, service: ChoirService) -> None:
        self._service = service

    @property
    def name(self) -> str:
        """``create_choir``."""
        return "create_choir"

    @property
    def description(self) -> str:
        """Description for the model."""
        return (
            "Create a choir. The first choir created becomes the default choir. Ask the user "
            "for the name; never invent it."
        )

    @property
    def arguments_model(self) -> type[CreateChoirArguments]:
        """The name of the choir."""
        return CreateChoirArguments

    async def execute(self, arguments: CreateChoirArguments, context: ToolContext) -> ToolResult:
        """Create the choir."""
        choir = await self._service.create(arguments.name)
        suffix = " It is the default choir." if choir.is_default else ""
        return ToolResult(
            text=f"The choir {choir.name} was created.{suffix}",
            structured={"choir": choir_data(choir)},
        )
