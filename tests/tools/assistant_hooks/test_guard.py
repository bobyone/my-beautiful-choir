# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests for the request adapter and its process entry point."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from tools.assistant_hooks.guard import MALFORMED_REQUEST, check_request
from tools.assistant_hooks.protection_rules import ENV_FILE_REASON, FORCE_PUSH_REASON

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    ("tool_name", "tool_input", "reason"),
    [
        ("Read", {"file_path": ".env"}, ENV_FILE_REASON),
        ("Read", {"file_path": ".env.example"}, None),
        ("WebSearch", {"query": ".env"}, None),
        ("Bash", {"command": "git status && git push --force"}, FORCE_PUSH_REASON),
        ("PowerShell", {"command": "Get-Content .env.local"}, ENV_FILE_REASON),
        (
            "apply_patch",
            {"command": "*** Begin Patch\n*** Add File: .env.example\n+SECRET=\n*** End Patch"},
            None,
        ),
        (
            "apply_patch",
            {
                "command": "*** Begin Patch\n*** Add File: readme.md\n+sample\n"
                "*** Update File: docs/config.md\n*** Move to: secrets/config.md\n*** End Patch"
            },
            ENV_FILE_REASON,
        ),
        ("apply_patch", {"command": "*** End Patch"}, MALFORMED_REQUEST),
        ("apply_patch", {"command": "*** Begin Patch\n*** End Patch"}, MALFORMED_REQUEST),
        ("Bash", {"command": ""}, MALFORMED_REQUEST),
        ("Read", {"file_path": []}, MALFORMED_REQUEST),
        ("Read", None, MALFORMED_REQUEST),
    ],
)
def test_request(tool_name: str, tool_input: object, reason: str | None) -> None:
    assert check_request({"tool_name": tool_name, "tool_input": tool_input}) == reason


@pytest.mark.parametrize(
    ("payload", "exit_code"),
    [
        ({"tool_name": "Bash", "tool_input": {"command": "git status"}}, 0),
        ({"tool_name": "Read", "tool_input": {"file_path": "secrets/fake-value"}}, 2),
        ("malformed", 2),
    ],
)
def test_guard_process(payload: object, exit_code: int) -> None:
    raw_input = payload if isinstance(payload, str) else json.dumps(payload)
    result = subprocess.run(
        [sys.executable, "-B", "-m", "tools.assistant_hooks.guard"],
        cwd=ROOT,
        input=raw_input,
        capture_output=True,
        encoding="utf-8",
        check=False,
        timeout=10,
    )
    assert result.returncode == exit_code
    assert result.stdout == ""
    if exit_code == 2:
        assert result.stderr.startswith("Blocked by project rules:")
        assert "fake-value" not in result.stderr
    else:
        assert result.stderr == ""
