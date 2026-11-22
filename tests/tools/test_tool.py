# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the default behaviour of the tool abstraction."""

import pytest
from pydantic import ValidationError

from my_beautiful_choir.tools.no_arguments import NoArguments
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class _MinimalTool(Tool[NoArguments]):
    @property
    def name(self) -> str:
        return "minimal"

    @property
    def description(self) -> str:
        return "Minimal tool."

    @property
    def arguments_model(self) -> type[NoArguments]:
        return NoArguments

    async def execute(self, arguments: NoArguments, context: ToolContext) -> ToolResult:
        return ToolResult(text="done")


def test_has_no_view_by_default() -> None:
    assert _MinimalTool().view is None


def test_no_arguments_rejects_any_argument() -> None:
    with pytest.raises(ValidationError):
        NoArguments.model_validate({"unexpected": 1})
