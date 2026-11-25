# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Decorator recording the metrics of a tool."""

import time

from pydantic import BaseModel

from my_beautiful_choir.monitoring.metrics import Metrics
from my_beautiful_choir.tools.errors import ToolCallSuspended
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult
from my_beautiful_choir.views.view import View


class MeteredTool[ArgumentsT: BaseModel](Tool[ArgumentsT]):
    """Wraps a tool and records the duration and outcome of each of its calls."""

    def __init__(self, inner: Tool[ArgumentsT], metrics: Metrics) -> None:
        self._inner = inner
        self._metrics = metrics

    @property
    def name(self) -> str:
        """Name of the wrapped tool."""
        return self._inner.name

    @property
    def description(self) -> str:
        """Description of the wrapped tool."""
        return self._inner.description

    @property
    def arguments_model(self) -> type[ArgumentsT]:
        """Arguments model of the wrapped tool."""
        return self._inner.arguments_model

    @property
    def view(self) -> View | None:
        """View of the wrapped tool."""
        return self._inner.view

    @property
    def read_only(self) -> bool:
        """Preserve the read-only annotation of the wrapped tool."""
        return self._inner.read_only

    @property
    def app_only(self) -> bool:
        """Visibility of the wrapped tool."""
        return self._inner.app_only

    async def execute(self, arguments: ArgumentsT, context: ToolContext) -> ToolResult:
        """Run the wrapped tool and record the call, whatever its outcome.

        A suspended call is not recorded: it is recorded when the client calls
        the tool again.
        """
        start = time.perf_counter()
        failed: bool | None = True
        try:
            result = await self._inner.execute(arguments, context)
            failed = False
            return result
        except ToolCallSuspended:
            failed = None
            raise
        finally:
            if failed is not None:
                self._metrics.record_tool_call(self.name, time.perf_counter() - start, failed)
