# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Integration tests of the elicitation confirmation, through the SDK in-memory client.

Each test runs with the initialize handshake ('legacy': the question is asked
during the call) and with protocol negotiation ('auto': from 2026-07-28, the
call ends with an input request and the client retries it).
"""

from typing import Any

import pytest
from mcp.client import Client
from mcp.client.context import ClientRequestContext
from mcp.client.session import ElicitationFnT
from mcp.types import ElicitRequestParams, ElicitResult, ErrorData, TextContent

from my_beautiful_choir.application.application_info import ApplicationInfo
from my_beautiful_choir.configuration.mode import Mode
from my_beautiful_choir.mcp.mcp_server_builder import McpServerBuilder
from my_beautiful_choir.tools.no_arguments import NoArguments
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult

INFO = ApplicationInfo("my-beautiful-choir", "1.2.3", Mode.PERSONAL)
QUESTION = "Delete the work Ave Maria and its 2 scores?"


class _AskingTool(Tool[NoArguments]):
    """Asks for a confirmation and returns the outcome as text."""

    @property
    def name(self) -> str:
        return "ask"

    @property
    def description(self) -> str:
        return "Ask for a confirmation."

    @property
    def arguments_model(self) -> type[NoArguments]:
        return NoArguments

    def __init__(self) -> None:
        self.executions = 0

    async def execute(self, arguments: NoArguments, context: ToolContext) -> ToolResult:
        self.executions += 1
        return ToolResult(text=await context.confirmation.ask(QUESTION))


def _answering(
    action: str, content: dict[str, Any] | None = None, questions: list[str] | None = None
) -> ElicitationFnT:
    async def callback(
        context: ClientRequestContext, params: ElicitRequestParams
    ) -> ElicitResult | ErrorData:
        if questions is not None:
            questions.append(params.message)
        return ElicitResult(action=action, content=content)  # type: ignore[arg-type]

    return callback


@pytest.fixture(params=["legacy", "auto"])
def mode(request: pytest.FixtureRequest) -> str:
    return str(request.param)


async def _outcome(
    mode: str, elicitation_callback: ElicitationFnT | None = None, tool: _AskingTool | None = None
) -> str:
    server = McpServerBuilder(INFO, [tool or _AskingTool()]).build()
    async with Client(server, mode=mode, elicitation_callback=elicitation_callback) as client:
        result = await client.call_tool("ask", {})
    assert not result.is_error
    [content] = result.content
    assert isinstance(content, TextContent)
    return content.text


@pytest.mark.anyio
async def test_accepted_and_checked_is_confirmed(mode: str) -> None:
    questions: list[str] = []
    callback = _answering("accept", {"confirmed": True}, questions)
    assert await _outcome(mode, callback) == "confirmed"
    assert questions == [QUESTION]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("action", "content"),
    [
        ("accept", {"confirmed": False}),
        ("accept", {"confirmed": "maybe"}),
        ("decline", None),
        ("cancel", None),
    ],
)
async def test_other_answers_are_refusals(
    mode: str, action: str, content: dict[str, Any] | None
) -> None:
    assert await _outcome(mode, _answering(action, content)) == "refused"


@pytest.mark.anyio
async def test_client_without_elicitation_is_unavailable(mode: str) -> None:
    assert await _outcome(mode) == "unavailable"


@pytest.mark.anyio
@pytest.mark.parametrize(("mode", "executions"), [("legacy", 1), ("auto", 2)])
async def test_tool_runs_again_when_the_client_retries(mode: str, executions: int) -> None:
    tool = _AskingTool()
    assert await _outcome(mode, _answering("accept", {"confirmed": True}), tool) == "confirmed"
    assert tool.executions == executions


@pytest.mark.anyio
async def test_client_error_during_the_call_is_unavailable() -> None:
    async def failing(context: ClientRequestContext, params: ElicitRequestParams) -> ErrorData:
        return ErrorData(code=-32603, message="no user")

    assert await _outcome("legacy", failing) == "unavailable"
