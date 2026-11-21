# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Adapter building an MCP SDK server from the application's tools and views.

This is the only module of the core that knows the MCP SDK: a breaking change
of the SDK is absorbed here.
"""

import inspect
import logging
from collections.abc import Awaitable, Callable, Sequence
from typing import Annotated, Any

from mcp.server.apps import Apps
from mcp.server.mcpserver import MCPServer
from mcp.types import CallToolResult, TextContent
from pydantic import Field

from my_beautiful_choir.application.application_info import ApplicationInfo
from my_beautiful_choir.tools.errors import ToolExecutionError
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_result import ToolResult

_LOGGER = logging.getLogger(__name__)

UNEXPECTED_ERROR_TEXT = (
    "The tool failed because of an unexpected error. "
    "The details are in the server logs; please report the problem if it persists."
)

ToolHandler = Callable[..., Awaitable[CallToolResult]]


def _text_result(text: str, is_error: bool = False) -> CallToolResult:
    return CallToolResult(content=[TextContent(type="text", text=text)], is_error=is_error)


def _to_call_tool_result(result: ToolResult) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=result.text)],
        structured_content=dict(result.structured) if result.structured else None,
    )


def _signature_of(tool: Tool[Any]) -> inspect.Signature:
    """Keyword-only parameters mirroring the fields of the tool's arguments model."""
    parameters = [
        inspect.Parameter(
            name,
            inspect.Parameter.KEYWORD_ONLY,
            annotation=Annotated[field.annotation, Field(description=field.description)],
            default=inspect.Parameter.empty if field.is_required() else field.default,
        )
        for name, field in tool.arguments_model.model_fields.items()
    ]
    return inspect.Signature(parameters, return_annotation=CallToolResult)


def _handler_for(tool: Tool[Any]) -> ToolHandler:
    """Function registered in the SDK for ``tool``.

    The SDK publishes the JSON Schema and validates the arguments from the
    function signature, generated from the tool's arguments model.
    """

    async def handler(**raw_arguments: object) -> CallToolResult:
        arguments = tool.arguments_model.model_validate(raw_arguments)
        try:
            return _to_call_tool_result(await tool.execute(arguments))
        except ToolExecutionError as error:
            return _text_result(str(error), is_error=True)
        except Exception:
            _LOGGER.exception("Unexpected error in tool", extra={"tool": tool.name})
            return _text_result(UNEXPECTED_ERROR_TEXT, is_error=True)

    handler.__name__ = tool.name
    handler.__signature__ = _signature_of(tool)  # type: ignore[attr-defined]
    return handler


class McpServerBuilder:
    """Builds an MCP server publishing the given tools and their views.

    Tools with a view are registered through the MCP Apps extension, with the
    view as a ``ui://`` resource; the others are plain tools.
    """

    def __init__(self, application_info: ApplicationInfo, tools: Sequence[Tool[Any]]) -> None:
        self._application_info = application_info
        self._tools = tools

    def build(self) -> MCPServer:
        """Return a new server.

        Raises:
            ViewNotFoundError: if the document of a view is missing.
        """
        apps = Apps()
        registered_views: set[str] = set()
        text_tools: list[Tool[Any]] = []
        for tool in self._tools:
            view = tool.view
            if view is None:
                text_tools.append(tool)
                continue
            if view.uri not in registered_views:
                apps.add_html_resource(view.uri, view.content())
                registered_views.add(view.uri)
            apps.tool(resource_uri=view.uri, name=tool.name, description=tool.description)(
                _handler_for(tool)
            )

        server = MCPServer(
            name=self._application_info.name,
            version=self._application_info.version,
            extensions=[apps],
        )
        for tool in text_tools:
            server.add_tool(_handler_for(tool), name=tool.name, description=tool.description)
        return server
