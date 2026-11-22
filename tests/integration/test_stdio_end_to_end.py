# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""End-to-end tests of personal mode: a real process spoken to over stdio."""

import json
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from my_beautiful_choir.views.packaged.packaged_view import packaged_views_directory
from tests.integration.stdio_session import TIMEOUT_SECONDS, StdioSession, launch_environment

LAUNCHER = Path(__file__).with_name("personal_mode_launcher.py")
ABOUT_URI = "ui://my-beautiful-choir/about.html"
DELETION_URI = "ui://my-beautiful-choir/deletion.html"
VIEWS = ("about.html", "deletion.html")


def _write_stub_views(directory: Path) -> None:
    for view in VIEWS:
        (directory / view).write_text(f"<p>{view.removesuffix('.html')}</p>", encoding="utf-8")


def _exchange_show_about(session: StdioSession) -> dict[str, Any]:
    """Handshake, list the tools, call show_about; return its result."""
    assert session.initialize()["serverInfo"]["name"] == "my-beautiful-choir"
    tools = {tool["name"]: tool for tool in session.request(2, "tools/list")["tools"]}
    assert tools["show_about"]["_meta"]["ui"]["resourceUri"] == ABOUT_URI
    call = session.request(3, "tools/call", {"name": "show_about", "arguments": {}})
    assert call["structuredContent"]["mode"] == "personal"
    assert call["content"][0]["text"].endswith(", personal mode.")
    return session.request(4, "resources/read", {"uri": ABOUT_URI})


@pytest.fixture
def launched(tmp_path: Path) -> Iterator[StdioSession]:
    """The real entry point, with stub views."""
    _write_stub_views(tmp_path)
    session = StdioSession([sys.executable, str(LAUNCHER), str(tmp_path)], tmp_path / "data")
    yield session
    session.kill()


def test_personal_mode_serves_show_about_over_stdio(launched: StdioSession) -> None:
    resource = _exchange_show_about(launched)
    assert resource["contents"][0]["text"] == "<p>about</p>"

    exit_code, stderr = launched.close()
    assert exit_code == 0, stderr
    assert launched.stdout_lines.empty()
    # logs go to stderr, as JSON
    messages = [json.loads(line)["message"] for line in stderr.splitlines() if line.startswith("{")]
    assert "Starting my-beautiful-choir" in messages
    assert "Data store ready" in messages


def _call(session: StdioSession, request_id: int, tool: str, **arguments: object) -> str:
    result = session.request(request_id, "tools/call", {"name": tool, "arguments": arguments})
    assert not result.get("isError"), result
    return str(result["content"][0]["text"])


def test_choirs_are_kept_in_the_data_directory(tmp_path: Path) -> None:
    _write_stub_views(tmp_path)
    command = [sys.executable, str(LAUNCHER), str(tmp_path)]
    first = StdioSession(command, tmp_path / "data")
    try:
        first.initialize()
        assert _call(first, 2, "create_choir", name="Chœur de Lyon").endswith("default choir.")
        assert first.close()[0] == 0
    finally:
        first.kill()
    second = StdioSession(command, tmp_path / "data")
    try:
        second.initialize()
        assert _call(second, 2, "list_choirs") == "1 choir(s): Chœur de Lyon (default)."
        assert second.close()[0] == 0
    finally:
        second.kill()
    assert (tmp_path / "data" / "my-beautiful-choir.sqlite3").is_file()


def test_missing_view_exits_with_4_without_writing_to_stdout(tmp_path: Path) -> None:
    completed = subprocess.run(  # noqa: S603
        [sys.executable, str(LAUNCHER), str(tmp_path)],
        input="",
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=TIMEOUT_SECONDS,
        env=launch_environment(tmp_path / "data"),
        check=False,
    )
    assert completed.returncode == 4
    assert completed.stdout == ""
    assert "[MBC-INSTALL]" in completed.stderr


@pytest.mark.skipif(
    not all(packaged_views_directory().joinpath(view).is_file() for view in VIEWS),
    reason="the user interface is not built (uv run nox -s ui)",
)
def test_module_serves_the_built_views_and_confirms_a_deletion(tmp_path: Path) -> None:
    session = StdioSession([sys.executable, "-m", "my_beautiful_choir"], tmp_path / "data")
    try:
        resource = _exchange_show_about(session)
        [contents] = resource["contents"]
        assert contents["mimeType"] == "text/html;profile=mcp-app"
        assert contents["text"].startswith("<!doctype html>")
        assert "<script" in contents["text"]

        tools = {tool["name"]: tool for tool in session.request(5, "tools/list")["tools"]}
        assert tools["delete_choir"]["_meta"]["ui"]["resourceUri"] == DELETION_URI
        assert tools["confirm_deletion"]["_meta"]["ui"] == {
            "resourceUri": DELETION_URI,
            "visibility": ["app"],
        }
        deletion_resource = session.request(6, "resources/read", {"uri": DELETION_URI})
        [deletion_view] = deletion_resource["contents"]
        assert deletion_view["mimeType"] == "text/html;profile=mcp-app"
        assert deletion_view["text"].startswith("<!doctype html>")
        assert "<script" in deletion_view["text"]
        assert "<style" in deletion_view["text"]

        choir = "Chœur de Lyon"
        _call(session, 7, "create_choir", name=choir)
        requested = session.request(
            8, "tools/call", {"name": "delete_choir", "arguments": {"choir": choir}}
        )
        assert not requested.get("isError"), requested
        deletion = requested["structuredContent"]
        assert deletion["status"] == "pending"
        assert deletion["deletion"]["name"] == choir
        assert choir in _call(session, 9, "list_choirs")

        confirmation = {
            "name": "confirm_deletion",
            "arguments": {"token": deletion["token"]},
        }
        confirmed = session.request(10, "tools/call", confirmation)
        assert confirmed["structuredContent"]["status"] == "deleted"
        assert session.request(11, "tools/call", confirmation)["isError"]
        assert choir not in _call(session, 12, "list_choirs")
        exit_code, stderr = session.close()
        assert exit_code == 0, stderr
    finally:
        session.kill()
