# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool abstraction."""

from abc import ABC, abstractmethod

from pydantic import BaseModel

from my_beautiful_choir.tools.tool_result import ToolResult
from my_beautiful_choir.views.view import View


class Tool[ArgumentsT: BaseModel](ABC):
    """An operation offered to the MCP client, independent of the MCP SDK.

    Its arguments are described by a pydantic model: the MCP layer publishes
    its JSON Schema and validates the arguments before calling ``execute``.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the tool, in snake case."""

    @property
    @abstractmethod
    def description(self) -> str:
        """English description telling the model when to use the tool."""

    @property
    @abstractmethod
    def arguments_model(self) -> type[ArgumentsT]:
        """Pydantic model of the arguments (``NoArguments`` for a tool without arguments)."""

    @property
    def view(self) -> View | None:
        """View displaying the result, or None for a text-only tool."""
        return None

    @abstractmethod
    async def execute(self, arguments: ArgumentsT) -> ToolResult:
        """Run the tool with validated arguments.

        Raises:
            ToolExecutionError: if the tool cannot complete.
        """
