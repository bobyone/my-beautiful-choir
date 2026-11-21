# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Test doubles of the abstractions, shared by the tests."""

from pydantic import BaseModel, Field

from my_beautiful_choir.monitoring.metrics import Metrics
from my_beautiful_choir.monitoring.metrics_export import MetricsExport
from my_beautiful_choir.tools.errors import ToolExecutionError
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_result import ToolResult
from my_beautiful_choir.views.view import View


class StubView(View):
    """View with fixed URI and content."""

    def __init__(self, uri: str = "ui://test/view.html", html: str = "<p>view</p>") -> None:
        self._uri = uri
        self._html = html

    @property
    def uri(self) -> str:
        return self._uri

    def content(self) -> str:
        return self._html


class StubArguments(BaseModel):
    """Arguments of the stub tool."""

    title: str = Field(description="Title to echo.")
    count: int = 1


class StubTool(Tool[StubArguments]):
    """Tool returning a fixed result, or failing on demand."""

    def __init__(self, name: str = "stub", view: View | None = None, fail: bool = False) -> None:
        self._name = name
        self._view = view
        self._fail = fail
        self.calls: list[StubArguments] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return "A stub tool."

    @property
    def arguments_model(self) -> type[StubArguments]:
        return StubArguments

    @property
    def view(self) -> View | None:
        return self._view

    async def execute(self, arguments: StubArguments) -> ToolResult:
        self.calls.append(arguments)
        if self._fail:
            raise ToolExecutionError("stub failure")
        return ToolResult(
            text=f"stub result for {arguments.title}",
            structured={"title": arguments.title, "count": arguments.count},
        )


class SpyMetrics(Metrics):
    """Metrics keeping every recorded measure."""

    def __init__(self) -> None:
        self.tool_calls: list[tuple[str, float, bool]] = []
        self.http_requests: list[tuple[str, str, int, float]] = []

    def record_tool_call(self, tool_name: str, duration_seconds: float, failed: bool) -> None:
        self.tool_calls.append((tool_name, duration_seconds, failed))

    def record_http_request(
        self, method: str, route: str, status_code: int, duration_seconds: float
    ) -> None:
        self.http_requests.append((method, route, status_code, duration_seconds))

    def export(self) -> MetricsExport:
        return MetricsExport(content_type="text/plain", body=b"spy")
