# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Integration tests of the HTTP transport."""

import socket
from collections.abc import Iterator

import anyio
import httpx
import pytest
from starlette.testclient import TestClient

from my_beautiful_choir.application.application_info import ApplicationInfo
from my_beautiful_choir.configuration.mode import Mode
from my_beautiful_choir.configuration.web_settings import WebSettings
from my_beautiful_choir.mcp.mcp_server_builder import McpServerBuilder
from my_beautiful_choir.monitoring.server.server_health_check import ServerHealthCheck
from my_beautiful_choir.transport.errors import PortUnavailableError
from my_beautiful_choir.transport.http.http_transport import HttpTransport
from tests.doubles import SpyMetrics, StubTool

INFO = ApplicationInfo("my-beautiful-choir", "1.2.3", Mode.WEB)
INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1"},
    },
}
MCP_HEADERS = {"Accept": "application/json, text/event-stream"}


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


class _Fixture:
    def __init__(self, settings: WebSettings | None = None) -> None:
        self.metrics = SpyMetrics()
        self.health = ServerHealthCheck()
        self.transport = HttpTransport(settings or WebSettings(), self.metrics, self.health)
        self.server = McpServerBuilder(INFO, [StubTool()]).build()


@pytest.fixture
def fixture() -> _Fixture:
    return _Fixture()


@pytest.fixture
def client(fixture: _Fixture) -> Iterator[TestClient]:
    app = fixture.transport.create_app(fixture.server)
    with TestClient(app, base_url="http://127.0.0.1:9000") as test_client:
        yield test_client


def test_health_is_unavailable_until_ready(fixture: _Fixture, client: TestClient) -> None:
    response = client.get("/healthz")
    assert (response.status_code, response.json()) == (503, {"status": "unavailable"})
    fixture.health.mark_ready()
    response = client.get("/healthz")
    assert (response.status_code, response.json()) == (200, {"status": "ready"})


def test_metrics_route_serves_the_export(client: TestClient) -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.text == "spy"


def test_requests_are_measured_with_bounded_routes(fixture: _Fixture, client: TestClient) -> None:
    client.get("/healthz")
    client.get("/unknown/path")
    routes = [(method, route, status) for method, route, status, _ in fixture.metrics.http_requests]
    assert routes == [("GET", "/healthz", 503), ("GET", "other", 404)]


def test_requests_carry_a_correlation_id(client: TestClient) -> None:
    generated = client.get("/healthz")
    assert generated.headers["X-Request-ID"]
    given = "0b8f6c3c-3f4e-4a4f-9a51-0a3e8a1d2b7c"
    reused = client.get("/healthz", headers={"X-Request-ID": given})
    assert reused.headers["X-Request-ID"] == given


def test_request_log_has_no_client_address(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("INFO")
    client.get("/healthz")
    [record] = [r for r in caplog.records if r.getMessage() == "HTTP request"]
    assert record.__dict__["route"] == "/healthz"
    assert "client" not in record.__dict__
    assert "127.0.0.1" not in str(record.__dict__)


def test_mcp_endpoint_accepts_local_host(client: TestClient) -> None:
    response = client.post("/mcp", json=INITIALIZE, headers=MCP_HEADERS)
    assert response.status_code == 200


def test_mcp_endpoint_rejects_unknown_host(client: TestClient) -> None:
    response = client.post(
        "/mcp", json=INITIALIZE, headers={**MCP_HEADERS, "Host": "evil.example.org"}
    )
    assert response.status_code == 421


def test_mcp_endpoint_accepts_configured_host() -> None:
    fixture = _Fixture(WebSettings(allowed_hosts=("choir.example.org",)))
    app = fixture.transport.create_app(fixture.server)
    with TestClient(app, base_url="http://choir.example.org") as test_client:
        response = test_client.post("/mcp", json=INITIALIZE, headers=MCP_HEADERS)
    assert response.status_code == 200


def test_port_in_use_is_reported() -> None:
    port = _free_port()
    with socket.socket() as occupant:
        occupant.bind(("127.0.0.1", port))
        occupant.listen()
        transport = HttpTransport(WebSettings(port=port), SpyMetrics(), ServerHealthCheck())
        with pytest.raises(PortUnavailableError) as raised:
            transport.bind()
    assert raised.value.exit_code == 3
    assert raised.value.error_code == "MBC-PORT"
    assert str(port) in raised.value.message


@pytest.mark.anyio
async def test_run_serves_until_stop_is_requested() -> None:
    port = _free_port()
    health = ServerHealthCheck()
    transport = HttpTransport(WebSettings(port=port), SpyMetrics(), health)
    server = McpServerBuilder(INFO, [StubTool()]).build()
    with anyio.fail_after(15):
        async with anyio.create_task_group() as group:
            group.start_soon(transport.run, server)
            async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}") as http:
                while True:
                    try:
                        response = await http.get("/healthz")
                    except httpx.ConnectError:
                        await anyio.sleep(0.05)
                        continue
                    if response.status_code == 200:
                        break
                    await anyio.sleep(0.05)
            transport.request_stop()
    assert response.json() == {"status": "ready"}
    assert health.status().value == "unavailable"


def test_request_stop_without_running_server_does_nothing() -> None:
    HttpTransport(WebSettings(), SpyMetrics(), ServerHealthCheck()).request_stop()
