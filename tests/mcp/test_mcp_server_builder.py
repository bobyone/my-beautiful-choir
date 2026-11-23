# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Integration tests of the MCP adapter, through the SDK in-memory client."""

from base64 import b64decode
from collections.abc import Sequence
from typing import Annotated, Any, Self

import pytest
from mcp.client import Client
from mcp.client.extension import ClientExtension, advertise
from mcp.server.apps import APP_MIME_TYPE, EXTENSION_ID
from mcp.types import BlobResourceContents, EmbeddedResource, TextContent
from pydantic import BaseModel, Field, model_validator

from my_beautiful_choir.application.application_info import ApplicationInfo
from my_beautiful_choir.configuration.mode import Mode
from my_beautiful_choir.errors import DomainError
from my_beautiful_choir.mcp.mcp_server_builder import (
    CONTEXT_PARAMETER,
    UNEXPECTED_ERROR_TEXT,
    McpServerBuilder,
    file_uri,
)
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_file import ToolFile
from my_beautiful_choir.tools.tool_result import ToolResult
from my_beautiful_choir.views.errors import ViewNotFoundError
from my_beautiful_choir.views.view import View
from tests.doubles import StubArguments, StubTool, StubView

INFO = ApplicationInfo("my-beautiful-choir", "1.2.3", Mode.PERSONAL)
VIEW_URI = "ui://my-beautiful-choir/stub.html"


class _CrashingTool(StubTool):
    async def execute(self, arguments: StubArguments, context: ToolContext) -> ToolResult:
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

    async def execute(self, arguments: _ConstrainedArguments, context: ToolContext) -> ToolResult:
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


class _NotFoundTool(StubTool):
    async def execute(self, arguments: StubArguments, context: ToolContext) -> ToolResult:
        raise DomainError("Work 42 not found.")


@pytest.mark.anyio
async def test_domain_error_is_returned_to_the_model() -> None:
    async with _client([_NotFoundTool()]) as client:
        result = await client.call_tool("stub", {"title": "x"})
    assert result.is_error
    assert _text(result.content[0]) == "Work 42 not found."


class _ReservedArguments(BaseModel):
    mbc_request_context: str


class _ReservedNameTool(_ConstrainedTool):
    @property
    def arguments_model(self) -> type[_ReservedArguments]:  # type: ignore[override]
        return _ReservedArguments


def test_reserved_argument_name_is_refused() -> None:
    assert CONTEXT_PARAMETER == "mbc_request_context"
    with pytest.raises(ValueError, match="reserved"):
        McpServerBuilder(INFO, [_ReservedNameTool()]).build()


@pytest.mark.anyio
async def test_app_only_tool_is_published_for_the_view_only() -> None:
    view = StubView(uri=VIEW_URI)
    tools = [StubTool(name="shown", view=view), StubTool(name="hidden", view=view, app_only=True)]
    async with _client(tools) as client:
        published = {tool.name: tool for tool in (await client.list_tools()).tools}
        assert published["shown"].meta == {"ui": {"resourceUri": VIEW_URI}}
        assert published["hidden"].meta == {"ui": {"resourceUri": VIEW_URI, "visibility": ["app"]}}


def test_app_only_tool_without_view_fails_the_build() -> None:
    with pytest.raises(ValueError, match="hidden"):
        McpServerBuilder(INFO, [StubTool(name="hidden", app_only=True)]).build()


class _FileTool(StubTool):
    def __init__(self, files: Sequence[ToolFile]) -> None:
        super().__init__(name="file")
        self._files = files

    async def execute(self, arguments: StubArguments, context: ToolContext) -> ToolResult:
        return ToolResult(text="here is the file", files=self._files)


@pytest.mark.anyio
async def test_files_are_returned_as_embedded_resources_after_the_text() -> None:
    content = bytes(range(256)) * 3
    files = [
        ToolFile("Ave/verum\\alto 100%.pdf", "application/pdf", content),
        ToolFile("Gloria.mxl", "application/vnd.recordare.musicxml", b""),
    ]
    async with _client([_FileTool(files)]) as client:
        result = await client.call_tool("file", {"title": "x"})
    assert not result.is_error
    text, first, second = result.content
    assert _text(text) == "here is the file"
    assert isinstance(first, EmbeddedResource)
    assert isinstance(first.resource, BlobResourceContents)
    assert first.resource.uri == "file:///Ave%2Fverum%5Calto%20100%25.pdf"
    assert first.resource.mime_type == "application/pdf"
    assert b64decode(first.resource.blob) == content
    assert isinstance(second, EmbeddedResource)
    assert isinstance(second.resource, BlobResourceContents)
    assert second.resource.uri == "file:///Gloria.mxl"
    assert second.resource.blob == ""


def test_file_uri_keeps_the_name_in_one_segment() -> None:
    assert file_uri("a/b\\c?d#e") == "file:///a%2Fb%5Cc%3Fd%23e"
    assert file_uri("Chœur.pdf") == "file:///Ch%C5%93ur.pdf"


@pytest.mark.anyio
async def test_result_without_files_has_only_its_text() -> None:
    async with _client([StubTool()]) as client:
        result = await client.call_tool("stub", {"title": "x"})
    assert len(result.content) == 1


class _ContextSpyTool(StubTool):
    def __init__(self) -> None:
        super().__init__(name="spy")
        self.contexts: list[ToolContext] = []

    async def execute(self, arguments: StubArguments, context: ToolContext) -> ToolResult:
        self.contexts.append(context)
        return ToolResult(text="seen")


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("extensions", "shows_views"),
    [
        ([], False),
        ([advertise(EXTENSION_ID, {"mimeTypes": [APP_MIME_TYPE]})], True),
        ([advertise(EXTENSION_ID, {})], False),
    ],
)
async def test_the_context_tells_whether_the_client_shows_views(
    extensions: list[ClientExtension], shows_views: bool
) -> None:
    tool = _ContextSpyTool()
    server = McpServerBuilder(INFO, [tool]).build()
    async with Client(server, raise_exceptions=False, extensions=extensions) as client:
        await client.call_tool("spy", {"title": "x"})
    [context] = tool.contexts
    assert context.client_shows_views is shows_views
