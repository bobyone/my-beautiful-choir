# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""JSON-RPC dialogue with a my-beautiful-choir process over stdio, for end-to-end tests."""

import json
import os
import queue
import subprocess
import threading
from collections.abc import Sequence
from pathlib import Path
from typing import IO, Any

from mcp.types import LATEST_PROTOCOL_VERSION

TIMEOUT_SECONDS = 30


def launch_environment(data_dir: Path) -> dict[str, str]:
    """Environment of a launched process: no bytecode, data in ``data_dir`` (never the user's)."""
    return {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "MBC_DATA_DIR": str(data_dir)}


class StdioSession:
    """Talks JSON-RPC to the process, one message at a time."""

    def __init__(self, command: Sequence[str], data_dir: Path) -> None:
        self.process = subprocess.Popen(  # noqa: S603
            list(command),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env=launch_environment(data_dir),
        )
        self.stdout_lines: queue.Queue[str] = queue.Queue()
        threading.Thread(target=self._pump, args=(self.process.stdout,), daemon=True).start()

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
        """Send a request and return the result of its response."""
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

    def initialize(self) -> dict[str, Any]:
        """Perform the MCP handshake and return the server's answer."""
        result = self.request(
            1,
            "initialize",
            {
                "protocolVersion": LATEST_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "end-to-end", "version": "1"},
            },
        )
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return result

    def close(self) -> tuple[int, str]:
        """Close stdin, wait for the process to stop, return its exit code and stderr."""
        assert self.process.stdin is not None
        self.process.stdin.close()
        _, stderr = self.process.communicate(timeout=TIMEOUT_SECONDS)
        return self.process.returncode, stderr

    def kill(self) -> None:
        """Stop the process if it is still running."""
        if self.process.poll() is None:
            self.process.kill()
            self.process.communicate()
