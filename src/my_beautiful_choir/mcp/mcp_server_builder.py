# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Adapter building an MCP SDK server from the application's tools and views.

With the MCP adapters of other notions (``*/mcp/``), this is the only code
that knows the MCP SDK: a breaking change of the SDK is absorbed here.
"""

import inspect
import logging
from base64 import b64encode
from collections.abc import Awaitable, Callable, Sequence
from typing import Annotated, Any, cast
from urllib.parse import quote

from mcp.server.apps import Apps
from mcp.server.mcpserver import Context, MCPServer
from mcp.types import (
    BlobResourceContents,
    CallToolResult,
    ContentBlock,
    EmbeddedResource,
    InputRequiredResult,
    TextContent,
)
from pydantic import Field, ValidationError
from pydantic.fields import FieldInfo

from my_beautiful_choir.application.application_info import ApplicationInfo
from my_beautiful_choir.confirmation.mcp.elicitation_confirmation import (
    ConfirmationInputRequired,
    ElicitationConfirmation,
)
from my_beautiful_choir.errors import DomainError
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_file import ToolFile
from my_beautiful_choir.tools.tool_result import ToolResult

_LOGGER = logging.getLogger(__name__)

CONTEXT_PARAMETER = "mbc_request_context"
"""Name of the handler parameter receiving the SDK request context."""

UNEXPECTED_ERROR_TEXT = (
    "The tool failed because of an unexpected error. "
    "The details are in the server logs; please report the problem if it persists."
)

ToolOutcome = CallToolResult | InputRequiredResult
ToolHandler = Callable[..., Awaitable[ToolOutcome]]


def _text_result(text: str, is_error: bool = False) -> CallToolResult:
    return CallToolResult(content=[TextContent(type="text", text=text)], is_error=is_error)


def file_uri(name: str) -> str:
    """URI carrying the file name of an embedded file, every reserved character encoded.

    Hosts take the file name from the last segment of the URI, as in the MCP
    Apps examples; ``/`` and ``\\`` are encoded so the name stays one segment.
    """
    return f"file:///{quote(name, safe='')}"


def _embedded(file: ToolFile) -> EmbeddedResource:
    return EmbeddedResource(
        type="resource",
        resource=BlobResourceContents(
            uri=file_uri(file.name),
            mime_type=file.media_type,
            blob=b64encode(file.content).decode("ascii"),
        ),
    )


def _to_call_tool_result(result: ToolResult) -> CallToolResult:
    content: list[ContentBlock] = [TextContent(type="text", text=result.text)]
    content.extend(_embedded(file) for file in result.files)
    return CallToolResult(
        content=content,
        structured_content=dict(result.structured) if result.structured else None,
    )


def _parameter_for(name: str, field: FieldInfo) -> inspect.Parameter:
    """Keyword-only parameter carrying the field's type, constraints, description and default."""
    metadata = (*field.metadata, Field(description=field.description))
    annotation: Any = Annotated[(field.annotation, *metadata)]
    if field.is_required():
        default: Any = inspect.Parameter.empty
    elif field.default_factory is not None:
        default = field.get_default(call_default_factory=True, validated_data={})
    else:
        default = field.default
    return inspect.Parameter(
        name, inspect.Parameter.KEYWORD_ONLY, annotation=annotation, default=default
    )


def _signature_of(tool: Tool[Any]) -> inspect.Signature:
    """Keyword-only parameters mirroring the fields of the tool's arguments model.

    A last parameter, annotated with the SDK ``Context``, receives the request
    context; the SDK leaves it out of the published schema.
    """
    fields = tool.arguments_model.model_fields
    if CONTEXT_PARAMETER in fields:
        raise ValueError(f"{tool.name}: '{CONTEXT_PARAMETER}' is reserved for the request context")
    parameters = [_parameter_for(name, field) for name, field in fields.items()]
    parameters.append(
        inspect.Parameter(CONTEXT_PARAMETER, inspect.Parameter.KEYWORD_ONLY, annotation=Context)
    )
    return inspect.Signature(parameters, return_annotation=ToolOutcome)


def _tool_context(request_context: Context) -> ToolContext:
    return ToolContext(confirmation=ElicitationConfirmation(request_context))


def _handler_for(tool: Tool[Any]) -> ToolHandler:
    """Function registered in the SDK for ``tool``.

    The SDK publishes the JSON Schema and validates the arguments from the
    function signature, generated from the tool's arguments model.
    """

    async def handler(**raw_arguments: object) -> ToolOutcome:
        request_context = cast(Context, raw_arguments.pop(CONTEXT_PARAMETER))
        try:
            arguments = tool.arguments_model.model_validate(raw_arguments)
            result = await tool.execute(arguments, _tool_context(request_context))
            return _to_call_tool_result(result)
        except ConfirmationInputRequired as required:
            return required.result
        except ValidationError as error:
            return _text_result(f"Invalid arguments: {error}", is_error=True)
        except DomainError as error:
            return _text_result(str(error), is_error=True)
        except Exception:
            _LOGGER.exception("Unexpected error in tool", extra={"tool": tool.name})
            return _text_result(UNEXPECTED_ERROR_TEXT, is_error=True)

    handler.__name__ = tool.name
    handler.__signature__ = _signature_of(tool)  # type: ignore[attr-defined]
    # The SDK finds the context parameter from the type hints.
    handler.__annotations__ = {CONTEXT_PARAMETER: Context, "return": ToolOutcome}
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
            ValueError: if an app-only tool has no view.
        """
        apps = Apps()
        registered_views: set[str] = set()
        text_tools: list[Tool[Any]] = []
        for tool in self._tools:
            view = tool.view
            if view is None:
                if tool.app_only:
                    raise ValueError(f"The app-only tool {tool.name} has no view")
                text_tools.append(tool)
                continue
            if view.uri not in registered_views:
                apps.add_html_resource(view.uri, view.content())
                registered_views.add(view.uri)
            apps.tool(
                resource_uri=view.uri,
                name=tool.name,
                description=tool.description,
                visibility=["app"] if tool.app_only else None,
            )(_handler_for(tool))

        server = MCPServer(
            name=self._application_info.name,
            version=self._application_info.version,
            extensions=[apps],
        )
        for tool in text_tools:
            server.add_tool(_handler_for(tool), name=tool.name, description=tool.description)
        return server
