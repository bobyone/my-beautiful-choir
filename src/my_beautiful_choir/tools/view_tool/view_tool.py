# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool whose result is displayed by a view."""

from abc import abstractmethod
from collections.abc import Mapping

from pydantic import BaseModel

from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult
from my_beautiful_choir.views.view import View


class ViewTool[ArgumentsT: BaseModel](Tool[ArgumentsT]):
    """Template method: the same data feeds both the view and the text result.

    Subclasses collect the data and describe it in text; ``execute`` assembles
    the result, so that the text always reflects what the view displays.
    """

    def __init__(self, view: View) -> None:
        self._view = view

    @property
    def view(self) -> View:
        """View displaying the result."""
        return self._view

    async def execute(self, arguments: ArgumentsT, context: ToolContext) -> ToolResult:
        """Collect the data, then return it with its text description."""
        data = await self._collect(arguments, context)
        return ToolResult(text=self._describe(data), structured=data)

    @abstractmethod
    async def _collect(self, arguments: ArgumentsT, context: ToolContext) -> Mapping[str, object]:
        """Collect the data displayed by the view.

        Raises:
            DomainError: if the data cannot be collected.
        """

    @abstractmethod
    def _describe(self, data: Mapping[str, object]) -> str:
        """Describe the data in self-sufficient English text."""
