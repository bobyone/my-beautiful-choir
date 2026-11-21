# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the metered tool decorator."""

import pytest

from my_beautiful_choir.tools.errors import ToolCallSuspended, ToolExecutionError
from my_beautiful_choir.tools.metered_tool import MeteredTool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult
from tests.doubles import SpyMetrics, StubArguments, StubTool, StubView, tool_context


@pytest.mark.anyio
async def test_successful_call_is_recorded() -> None:
    metrics = SpyMetrics()
    inner = StubTool(name="stub")
    arguments = StubArguments(title="Ave Maria")
    context = tool_context()
    result = await MeteredTool(inner, metrics).execute(arguments, context)
    assert result.text == "stub result for Ave Maria"
    assert inner.calls == [arguments]
    [(name, duration, failed)] = metrics.tool_calls
    assert (name, failed) == ("stub", False)
    assert duration >= 0


@pytest.mark.anyio
async def test_failed_call_is_recorded_and_raised() -> None:
    metrics = SpyMetrics()
    with pytest.raises(ToolExecutionError):
        await MeteredTool(StubTool(fail=True), metrics).execute(
            StubArguments(title="x"), tool_context()
        )
    assert [failed for _, _, failed in metrics.tool_calls] == [True]


def test_delegates_its_description_to_the_inner_tool() -> None:
    view = StubView()
    inner = StubTool(name="stub", view=view)
    tool = MeteredTool(inner, SpyMetrics())
    assert tool.name == "stub"
    assert tool.description == inner.description
    assert tool.arguments_model is StubArguments
    assert tool.view is view


class _SuspendingTool(StubTool):
    async def execute(self, arguments: StubArguments, context: ToolContext) -> ToolResult:
        raise ToolCallSuspended("waiting for the user")


@pytest.mark.anyio
async def test_suspended_call_is_not_recorded() -> None:
    metrics = SpyMetrics()
    with pytest.raises(ToolCallSuspended):
        await MeteredTool(_SuspendingTool(), metrics).execute(
            StubArguments(title="x"), tool_context()
        )
    assert metrics.tool_calls == []
