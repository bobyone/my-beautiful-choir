# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the Claude Code guard hook (.claude/hooks/guard.py)."""

import importlib.util
import io
import json
from pathlib import Path
from types import ModuleType

import pytest

GUARD_PATH = Path(__file__).parents[2] / ".claude" / "hooks" / "guard.py"


def _load_guard() -> ModuleType:
    spec = importlib.util.spec_from_file_location("guard", GUARD_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load_guard()


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        "/project/.env",
        r"C:\project\.env.local",
        ".env.production",
        "certs/server.pem",
        "id.key",
        "secrets/token.txt",
        "C:/project/.ENV",
        ".Env.local",
    ],
)
def test_file_tools_block_secret_files(path: str) -> None:
    assert guard.find_violation("Read", {"file_path": path}) == guard.ENV_FILE_REASON


@pytest.mark.parametrize(
    "path",
    [".env.example", ".ENV.EXAMPLE", "docs/environment.md", "src/settings.py", "keyboard.py"],
)
def test_file_tools_allow_other_files(path: str) -> None:
    assert guard.find_violation("Read", {"file_path": path}) is None


def test_grep_on_env_file_is_blocked() -> None:
    assert guard.find_violation("Grep", {"pattern": "TOKEN", "path": ".env"}) is not None


@pytest.mark.parametrize(
    "command",
    [
        "cat .env",
        "cat .ENV",
        "Get-Content .env.local",
        "type C:\\app\\.env",
        "source ./.env && run",
        'git commit -m "$(cat .env)"',
        "git commit -m 'x' && cat .env",
    ],
)
def test_shell_reading_env_file_is_blocked(command: str) -> None:
    assert guard.find_violation("Bash", {"command": command}) == guard.ENV_FILE_REASON


@pytest.mark.parametrize(
    "command",
    ["cat .env.example", "node -e 'process.env.HOME'", "python -c 'import os; os.environ'"],
)
def test_shell_allowed_env_references(command: str) -> None:
    assert guard.find_violation("Bash", {"command": command}) is None


@pytest.mark.parametrize(
    "command",
    [
        "git push --force",
        "git push -f origin main",
        "git push --force-with-lease",
        "git push origin +main",
        "git -C repo push -uf origin x",
    ],
)
def test_force_push_is_blocked(command: str) -> None:
    assert guard.find_violation("PowerShell", {"command": command}) == guard.FORCE_PUSH_REASON


@pytest.mark.parametrize(
    "command",
    [
        "git commit --no-verify -m x",
        "git commit -nm x",
        "git push --no-verify",
        "git -c core.hooksPath=/dev/null commit -m x",
        "SKIP=nox-check git commit -m x",
        "export SKIP=dco-sign-off; git commit -m x",
        "$env:SKIP='nox-check'; git commit -m x",
        "PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m x",
        "git commit -m 'x' -n",
    ],
)
def test_hook_bypass_is_blocked(command: str) -> None:
    assert guard.find_violation("Bash", {"command": command}) == guard.NO_VERIFY_REASON


@pytest.mark.parametrize(
    "command",
    [
        "git push -u origin 1-initialize-project",
        "git commit -s -m x",
        "uv run nox",
        'git commit -s -m "Never commit secrets"',
        "git commit -m 'Use the nox -n flag'",
        'git commit --message="Document .env.example and --no-verify"',
    ],
)
def test_regular_git_commands_are_allowed(command: str) -> None:
    assert guard.find_violation("Bash", {"command": command}) is None


def test_other_tools_are_allowed() -> None:
    assert guard.find_violation("WebSearch", {"query": ".env"}) is None


def test_main_blocks_with_exit_code_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = {"tool_name": "Read", "tool_input": {"file_path": ".env"}}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    assert guard.main() == 2
    assert "Blocked by project rules" in capsys.readouterr().err


def test_main_allows_with_exit_code_0(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"tool_name": "Read", "tool_input": {"file_path": "README.md"}}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    assert guard.main() == 0
