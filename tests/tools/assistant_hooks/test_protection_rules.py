# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests for the shared assistant protection rules."""

import pytest

from tools.assistant_hooks import protection_rules as rules


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
    assert rules.check_path(path) == rules.ENV_FILE_REASON


@pytest.mark.parametrize(
    "path",
    [".env.example", ".ENV.EXAMPLE", "docs/environment.md", "src/settings.py", "keyboard.py"],
)
def test_file_tools_allow_other_files(path: str) -> None:
    assert rules.check_path(path) is None


def test_grep_on_env_file_is_blocked() -> None:
    assert rules.check_path(".env") is not None


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
    assert rules.check_command(command) == rules.ENV_FILE_REASON


@pytest.mark.parametrize(
    "command",
    ["cat .env.example", "node -e 'process.env.HOME'", "python -c 'import os; os.environ'"],
)
def test_shell_allowed_env_references(command: str) -> None:
    assert rules.check_command(command) is None


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
    assert rules.check_command(command) == rules.FORCE_PUSH_REASON


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
    assert rules.check_command(command) == rules.NO_VERIFY_REASON


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
    assert rules.check_command(command) is None


@pytest.mark.parametrize(
    "continuation",
    ["\\\n", "\\\r\n", "`\n", "`\r\n"],
)
@pytest.mark.parametrize(
    ("command", "reason"),
    [
        ("git push {}--force", rules.FORCE_PUSH_REASON),
        ("git {}push origin +main", rules.FORCE_PUSH_REASON),
        ("git push --fo{}rce", rules.FORCE_PUSH_REASON),
        ("git commit {}--no-verify", rules.NO_VERIFY_REASON),
        ("git commit -{}n", rules.NO_VERIFY_REASON),
        ("git status && git push --no-{}verify", rules.NO_VERIFY_REASON),
        ("git push {}origin main", None),
        ("cat .env.{}example", None),
    ],
)
def test_shell_line_continuations(continuation: str, command: str, reason: str | None) -> None:
    assert rules.check_command(command.format(continuation)) == reason


@pytest.mark.parametrize("line_break", ["\n", "\\\\\n", "``\r\n"])
def test_shell_command_boundaries_remain_separate(line_break: str) -> None:
    assert rules.check_command(f"git status {line_break}echo --no-verify") is None
