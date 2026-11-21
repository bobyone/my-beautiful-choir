# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the metered tool decorator."""

import pytest

from my_beautiful_choir.tools.errors import ToolExecutionError
from my_beautiful_choir.tools.metered_tool import MeteredTool
from tests.doubles import SpyMetrics, StubTool, StubView


@pytest.mark.anyio
async def test_successful_call_is_recorded() -> None:
    metrics = SpyMetrics()
    inner = StubTool(name="stub")
    result = await MeteredTool(inner, metrics).execute({"a": 1})
    assert result.text == "stub result"
    assert inner.calls == [{"a": 1}]
    [(name, duration, failed)] = metrics.tool_calls
    assert (name, failed) == ("stub", False)
    assert duration >= 0


@pytest.mark.anyio
async def test_failed_call_is_recorded_and_raised() -> None:
    metrics = SpyMetrics()
    with pytest.raises(ToolExecutionError):
        await MeteredTool(StubTool(fail=True), metrics).execute({})
    assert [failed for _, _, failed in metrics.tool_calls] == [True]


def test_delegates_its_description_to_the_inner_tool() -> None:
    view = StubView()
    inner = StubTool(name="stub", view=view)
    tool = MeteredTool(inner, SpyMetrics())
    assert tool.name == "stub"
    assert tool.description == inner.description
    assert tool.input_schema == inner.input_schema
    assert tool.view is view
