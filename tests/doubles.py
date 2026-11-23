# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Test doubles of the abstractions, shared by the tests."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.authorization.authorization import Authorization
from my_beautiful_choir.authorization.errors import AccessDeniedError
from my_beautiful_choir.authorization.permission import Permission
from my_beautiful_choir.clock.clock import Clock
from my_beautiful_choir.confirmation.confirmation_outcome import ConfirmationOutcome
from my_beautiful_choir.confirmation.confirmation_requester import ConfirmationRequester
from my_beautiful_choir.monitoring.metrics import Metrics
from my_beautiful_choir.monitoring.metrics_export import MetricsExport
from my_beautiful_choir.tools.errors import ToolExecutionError
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.tool_context import ToolContext
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

    def __init__(
        self,
        name: str = "stub",
        view: View | None = None,
        fail: bool = False,
        app_only: bool = False,
    ) -> None:
        self._name = name
        self._view = view
        self._fail = fail
        self._app_only = app_only
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

    @property
    def app_only(self) -> bool:
        return self._app_only

    async def execute(self, arguments: StubArguments, context: ToolContext) -> ToolResult:
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


class StubConfirmation(ConfirmationRequester):
    """Confirmation requester giving a fixed answer and keeping the questions asked."""

    def __init__(self, outcome: ConfirmationOutcome = ConfirmationOutcome.CONFIRMED) -> None:
        self.outcome = outcome
        self.questions: list[str] = []

    async def ask(
        self, question: str, *, scope: str = "", keep: Callable[[], str] | None = None
    ) -> ConfirmationOutcome:
        self.questions.append(question)
        return self.outcome


def tool_context(
    confirmation: ConfirmationRequester | None = None, client_shows_views: bool = False
) -> ToolContext:
    """Context of a tool call in tests; confirmations are accepted by default."""
    return ToolContext(
        confirmation=confirmation or StubConfirmation(), client_shows_views=client_shows_views
    )


class FakeClock(Clock):
    """Clock at a fixed time, moved forward by the tests."""

    def __init__(self, start: datetime = datetime(2026, 11, 21, 12, 0, tzinfo=UTC)) -> None:
        self.start = start
        self.current = start

    def now(self) -> datetime:
        return self.current

    def advance(self, delta: timedelta) -> None:
        self.current += delta


class DenyingAuthorization(Authorization):
    """Authorization refusing the given permissions, and allowing the others."""

    def __init__(self, *denied: Permission) -> None:
        self.denied = set(denied)

    def require(self, permission: Permission, choir_id: UUID | None = None) -> None:
        if permission in self.denied:
            raise AccessDeniedError(f"Permission {permission} denied.")
