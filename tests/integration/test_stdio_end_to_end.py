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


def _exchange_show_about(session: StdioSession) -> dict[str, Any]:
    """Handshake, list the tools, call show_about; return its result."""
    assert session.initialize()["serverInfo"]["name"] == "my-beautiful-choir"
    [tool] = session.request(2, "tools/list")["tools"]
    assert tool["name"] == "show_about"
    assert tool["_meta"]["ui"]["resourceUri"] == ABOUT_URI
    call = session.request(3, "tools/call", {"name": "show_about", "arguments": {}})
    assert call["structuredContent"]["mode"] == "personal"
    assert call["content"][0]["text"].endswith(", personal mode.")
    return session.request(4, "resources/read", {"uri": ABOUT_URI})


@pytest.fixture
def launched(tmp_path: Path) -> Iterator[StdioSession]:
    """The real entry point, with a stub view."""
    (tmp_path / "about.html").write_text("<p>about</p>", encoding="utf-8")
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
    not packaged_views_directory().joinpath("about.html").is_file(),
    reason="the user interface is not built (uv run nox -s ui)",
)
def test_module_serves_the_built_view(tmp_path: Path) -> None:
    session = StdioSession([sys.executable, "-m", "my_beautiful_choir"], tmp_path / "data")
    try:
        resource = _exchange_show_about(session)
        [contents] = resource["contents"]
        assert contents["mimeType"] == "text/html;profile=mcp-app"
        assert contents["text"].startswith("<!doctype html>")
        assert "<script" in contents["text"]
        exit_code, stderr = session.close()
        assert exit_code == 0, stderr
    finally:
        session.kill()
