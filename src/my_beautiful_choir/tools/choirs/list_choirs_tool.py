# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool listing the choirs."""

from my_beautiful_choir.choirs.choir_service import ChoirService
from my_beautiful_choir.tools.choirs.choir_data import choir_data, choir_label
from my_beautiful_choir.tools.no_arguments import NoArguments
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class ListChoirsTool(Tool[NoArguments]):
    """Lists the choirs."""

    def __init__(self, service: ChoirService) -> None:
        self._service = service

    @property
    def name(self) -> str:
        """``list_choirs``."""
        return "list_choirs"

    @property
    def description(self) -> str:
        """Description for the model."""
        return (
            "List the user's choirs and tell which one is the default choir, used when a "
            "request names no choir."
        )

    @property
    def arguments_model(self) -> type[NoArguments]:
        """No argument."""
        return NoArguments

    async def execute(self, arguments: NoArguments, context: ToolContext) -> ToolResult:
        """List the choirs, the oldest first."""
        choirs = await self._service.list_choirs()
        if not choirs:
            text = (
                "No choir exists yet. Ask the user for the name of their first choir, "
                "then create it."
            )
        else:
            text = f"{len(choirs)} choir(s): " + ", ".join(choir_label(c) for c in choirs) + "."
        return ToolResult(text=text, structured={"choirs": [choir_data(c) for c in choirs]})
