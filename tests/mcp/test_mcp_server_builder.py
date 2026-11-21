# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Integration tests of the MCP adapter, through the SDK in-memory client."""

from collections.abc import Sequence
from typing import Annotated, Any, Self

import pytest
from mcp.client import Client
from mcp.types import TextContent
from pydantic import BaseModel, Field, model_validator

from my_beautiful_choir.application.application_info import ApplicationInfo
from my_beautiful_choir.configuration.mode import Mode
from my_beautiful_choir.mcp.mcp_server_builder import UNEXPECTED_ERROR_TEXT, McpServerBuilder
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_result import ToolResult
from my_beautiful_choir.views.errors import ViewNotFoundError
from my_beautiful_choir.views.view import View
from tests.doubles import StubArguments, StubTool, StubView

INFO = ApplicationInfo("my-beautiful-choir", "1.2.3", Mode.PERSONAL)
VIEW_URI = "ui://my-beautiful-choir/stub.html"


class _CrashingTool(StubTool):
    async def execute(self, arguments: StubArguments) -> ToolResult:
        raise RuntimeError("boom")


class _MissingView(View):
    @property
    def uri(self) -> str:
        return VIEW_URI

    def content(self) -> str:
        raise ViewNotFoundError(VIEW_URI)


class _ConstrainedArguments(BaseModel):
    voices: Annotated[int, Field(ge=1, description="Number of voices.")] = 4
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _no_reserved_tag(self) -> Self:
        if "reserved" in self.tags:
            raise ValueError("the reserved tag cannot be used")
        return self


class _ConstrainedTool(Tool[_ConstrainedArguments]):
    def __init__(self) -> None:
        self.calls: list[_ConstrainedArguments] = []

    @property
    def name(self) -> str:
        return "constrained"

    @property
    def description(self) -> str:
        return "A tool with constrained arguments."

    @property
    def arguments_model(self) -> type[_ConstrainedArguments]:
        return _ConstrainedArguments

    async def execute(self, arguments: _ConstrainedArguments) -> ToolResult:
        self.calls.append(arguments)
        return ToolResult(text="done")


def _client(tools: Sequence[Tool[Any]]) -> Client:
    return Client(McpServerBuilder(INFO, tools).build(), raise_exceptions=False)


def _text(content: object) -> str:
    assert isinstance(content, TextContent)
    return content.text


@pytest.mark.anyio
async def test_view_tool_is_published_with_its_view() -> None:
    tool = StubTool(name="stub", view=StubView(uri=VIEW_URI, html="<p>stub view</p>"))
    async with _client([tool]) as client:
        [published] = (await client.list_tools()).tools
        assert published.name == "stub"
        assert published.description == "A stub tool."
        assert published.meta == {"ui": {"resourceUri": VIEW_URI}}
        assert published.input_schema["required"] == ["title"]
        assert published.input_schema["properties"]["title"]["description"] == "Title to echo."
        resource = await client.read_resource(VIEW_URI)
        [contents] = resource.contents
        assert contents.mime_type == "text/html;profile=mcp-app"
        assert getattr(contents, "text", None) == "<p>stub view</p>"


@pytest.mark.anyio
async def test_call_returns_text_and_structured_content() -> None:
    tool = StubTool(view=StubView(uri=VIEW_URI))
    async with _client([tool]) as client:
        result = await client.call_tool("stub", {"title": "Ave Maria", "count": 2})
    assert not result.is_error
    assert _text(result.content[0]) == "stub result for Ave Maria"
    assert result.structured_content == {"title": "Ave Maria", "count": 2}
    assert tool.calls == [StubArguments(title="Ave Maria", count=2)]


@pytest.mark.anyio
async def test_invalid_arguments_are_rejected_before_execution() -> None:
    tool = StubTool()
    async with _client([tool]) as client:
        result = await client.call_tool("stub", {"count": "many"})
    assert result.is_error
    assert tool.calls == []


@pytest.mark.anyio
async def test_schema_keeps_constraints_and_default_factories() -> None:
    async with _client([_ConstrainedTool()]) as client:
        [published] = (await client.list_tools()).tools
    properties = published.input_schema["properties"]
    assert properties["voices"]["minimum"] == 1
    assert properties["voices"]["default"] == 4
    assert properties["voices"]["description"] == "Number of voices."
    assert properties["tags"]["default"] == []


@pytest.mark.anyio
async def test_defaults_and_constraints_apply_to_calls() -> None:
    tool = _ConstrainedTool()
    async with _client([tool]) as client:
        accepted = await client.call_tool("constrained", {})
        too_few = await client.call_tool("constrained", {"voices": 0})
    assert not accepted.is_error
    assert too_few.is_error
    assert tool.calls == [_ConstrainedArguments(voices=4, tags=[])]


@pytest.mark.anyio
async def test_model_validation_error_is_returned_to_the_model() -> None:
    tool = _ConstrainedTool()
    async with _client([tool]) as client:
        result = await client.call_tool("constrained", {"tags": ["reserved"]})
    assert result.is_error
    assert "the reserved tag cannot be used" in _text(result.content[0])
    assert tool.calls == []


@pytest.mark.anyio
async def test_tool_execution_error_is_returned_to_the_model() -> None:
    async with _client([StubTool(fail=True)]) as client:
        result = await client.call_tool("stub", {"title": "x"})
    assert result.is_error
    assert _text(result.content[0]) == "stub failure"


@pytest.mark.anyio
async def test_unexpected_error_is_hidden_and_logged(caplog: pytest.LogCaptureFixture) -> None:
    async with _client([_CrashingTool()]) as client:
        result = await client.call_tool("stub", {"title": "x"})
    assert result.is_error
    assert _text(result.content[0]) == UNEXPECTED_ERROR_TEXT
    assert "boom" not in _text(result.content[0])
    assert any(record.exc_info for record in caplog.records)


@pytest.mark.anyio
async def test_text_only_tool_has_no_view() -> None:
    async with _client([StubTool(name="plain")]) as client:
        [published] = (await client.list_tools()).tools
        result = await client.call_tool("plain", {"title": "x"})
    assert published.name == "plain"
    assert not (published.meta or {}).get("ui")
    assert not result.is_error


@pytest.mark.anyio
async def test_view_shared_by_two_tools_is_registered_once() -> None:
    view = StubView(uri=VIEW_URI)
    tools = [StubTool(name="first", view=view), StubTool(name="second", view=view)]
    async with _client(tools) as client:
        resources = (await client.list_resources()).resources
    assert [str(resource.uri) for resource in resources] == [VIEW_URI]


@pytest.mark.anyio
async def test_server_reports_application_name_and_version() -> None:
    async with _client([]) as client:
        server_info = client.server_info
    assert server_info is not None
    assert (server_info.name, server_info.version) == ("my-beautiful-choir", "1.2.3")


def test_missing_view_fails_the_build() -> None:
    with pytest.raises(ViewNotFoundError):
        McpServerBuilder(INFO, [StubTool(view=_MissingView())]).build()
