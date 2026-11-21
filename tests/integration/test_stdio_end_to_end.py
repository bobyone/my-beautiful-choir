# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""End-to-end test of personal mode: a real process spoken to over stdio."""

import json
import os
import queue
import subprocess
import sys
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import IO, Any

import pytest
from mcp.types import LATEST_PROTOCOL_VERSION

LAUNCHER = Path(__file__).with_name("personal_mode_launcher.py")
TIMEOUT_SECONDS = 30


class _StdioSession:
    """Talks JSON-RPC to the process, one message at a time."""

    def __init__(self, views: Path) -> None:
        self.process = subprocess.Popen(  # noqa: S603
            [sys.executable, str(LAUNCHER), str(views)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.stdout_lines: queue.Queue[str] = queue.Queue()
        self._stdout_reader = threading.Thread(
            target=self._pump, args=(self.process.stdout,), daemon=True
        )
        self._stdout_reader.start()

    def _pump(self, stream: IO[str] | None) -> None:
        assert stream is not None
        for line in stream:
            self.stdout_lines.put(line)

    def send(self, message: dict[str, Any]) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def request(
        self, identifier: int, method: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        message: dict[str, Any] = {"jsonrpc": "2.0", "id": identifier, "method": method}
        if params is not None:
            message["params"] = params
        self.send(message)
        while True:
            line = self.stdout_lines.get(timeout=TIMEOUT_SECONDS)
            response = json.loads(line)  # stdout carries only JSON-RPC messages
            assert response["jsonrpc"] == "2.0"
            if response.get("id") == identifier:
                result: dict[str, Any] = response["result"]
                return result

    def close(self) -> tuple[int, str]:
        """Close stdin, wait for the process to stop, return its exit code and stderr."""
        assert self.process.stdin is not None
        self.process.stdin.close()
        _, stderr = self.process.communicate(timeout=TIMEOUT_SECONDS)
        return self.process.returncode, stderr


@pytest.fixture
def session(tmp_path: Path) -> Iterator[_StdioSession]:
    (tmp_path / "about.html").write_text("<p>about</p>", encoding="utf-8")
    stdio_session = _StdioSession(tmp_path)
    yield stdio_session
    if stdio_session.process.poll() is None:
        stdio_session.process.kill()
        stdio_session.process.communicate()


def test_personal_mode_serves_show_about_over_stdio(session: _StdioSession) -> None:
    initialized = session.request(
        1,
        "initialize",
        {
            "protocolVersion": LATEST_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "end-to-end", "version": "1"},
        },
    )
    assert initialized["serverInfo"]["name"] == "my-beautiful-choir"
    session.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    [tool] = session.request(2, "tools/list")["tools"]
    assert tool["name"] == "show_about"
    assert tool["_meta"]["ui"]["resourceUri"] == "ui://my-beautiful-choir/about.html"

    call = session.request(3, "tools/call", {"name": "show_about", "arguments": {}})
    assert call["structuredContent"]["mode"] == "personal"
    assert call["content"][0]["text"].endswith(", personal mode.")

    exit_code, stderr = session.close()
    assert exit_code == 0, stderr
    assert session.stdout_lines.empty()
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
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        check=False,
    )
    assert completed.returncode == 4
    assert completed.stdout == ""
    assert "[MBC-INSTALL]" in completed.stderr
