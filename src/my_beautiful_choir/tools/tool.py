# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool abstraction."""

from abc import ABC, abstractmethod
from collections.abc import Mapping

from my_beautiful_choir.tools.tool_result import ToolResult
from my_beautiful_choir.views.view import View

EMPTY_INPUT_SCHEMA: Mapping[str, object] = {"type": "object", "properties": {}}


class Tool(ABC):
    """An operation offered to the MCP client, independent of the MCP SDK."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the tool, in snake case."""

    @property
    @abstractmethod
    def description(self) -> str:
        """English description telling the model when to use the tool."""

    @property
    def input_schema(self) -> Mapping[str, object]:
        """JSON Schema of the arguments; no argument by default."""
        return EMPTY_INPUT_SCHEMA

    @property
    def view(self) -> View | None:
        """View displaying the result, or None for a text-only tool."""
        return None

    @abstractmethod
    async def execute(self, arguments: Mapping[str, object]) -> ToolResult:
        """Run the tool.

        Raises:
            ToolExecutionError: if the tool cannot complete.
        """
