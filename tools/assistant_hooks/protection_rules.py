# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Identify protected paths and prohibited commands without executing requests."""

import re
from pathlib import PurePath

FILE_TOOLS = frozenset({"Read", "Edit", "MultiEdit", "Write", "NotebookEdit", "Grep", "Glob"})
SHELL_TOOLS = frozenset({"Bash", "PowerShell"})
PATH_KEYS = ("file_path", "notebook_path", "path", "pattern", "glob")

# Case-insensitive: Windows and macOS file systems open .env for .ENV.
_ENV_FILE = re.compile(r"(?:^|(?<=[\s'\"/\\=<>:(]))\.env(?:\.[\w-]+)*(?![\w])", re.IGNORECASE)
_SECRET_PATH = re.compile(r"(?:\.pem|\.key)$|(?:^|[/\\])secrets(?:[/\\]|$)", re.IGNORECASE)
_SEGMENT = r"[^;&|\n]*"
_FORCE_PUSH = re.compile(
    rf"\bgit\b{_SEGMENT}\bpush\b{_SEGMENT}(?:\s--force(?:-with-lease|-if-includes)?\b|\s-[a-zA-Z]*f[a-zA-Z]*\b|\s\+\S)"
)
_NO_VERIFY = re.compile(rf"\bgit\b{_SEGMENT}\s--no-verify\b")
_COMMIT_NO_VERIFY = re.compile(rf"\bgit\b{_SEGMENT}\bcommit\b{_SEGMENT}\s-[a-zA-Z]*n[a-zA-Z]*\b")
_HOOKS_PATH = re.compile(r"core\.hooksPath", re.IGNORECASE)
# pre-commit skips the hooks listed in SKIP, and runs without configuration with this variable.
_SKIP_HOOKS = re.compile(
    r"(?:^|[\s;&|(])(?:\$env:)?(?:SKIP|PRE_COMMIT_ALLOW_NO_CONFIG)\s*=", re.IGNORECASE
)
_COMMIT = re.compile(rf"\bgit\b{_SEGMENT}\bcommit\b")
# Quoted commit messages are literal text: their content is not checked. Double-quoted
# messages containing an expansion ($, `) are kept, since the shell would run it.
_QUOTED_MESSAGE = re.compile(r"""(\s(?:-[a-zA-Z]*m|--message)(?:\s+|=))(?:'[^']*'|"[^"$`]*")""")

ENV_FILE_REASON = (
    "Environment configuration files and secrets must never be read: "
    "use the matching .example file instead."
)
FORCE_PUSH_REASON = "Forced pushes require the maintainer's explicit agreement."
NO_VERIFY_REASON = "Git hooks must never be bypassed: fix the failing check instead."


def _mentions_env_file(text: str) -> bool:
    return any(
        not match.group(0).lower().endswith(".example") for match in _ENV_FILE.finditer(text)
    )


def _is_secret_path(path: str) -> bool:
    name = PurePath(path.replace("\\", "/")).name
    return _mentions_env_file(name) or bool(_SECRET_PATH.search(path))


def check_path(path: str) -> str | None:
    """Return a refusal reason when a request names a protected resource."""
    return ENV_FILE_REASON if _is_secret_path(path) else None


def check_command(raw_command: str) -> str | None:
    """Return the reason a command cannot proceed, or None."""
    command = (
        _QUOTED_MESSAGE.sub(r"\1''", raw_command) if _COMMIT.search(raw_command) else raw_command
    )
    tokens = (token.strip("'\"") for token in command.split())
    if _mentions_env_file(command) or any(_SECRET_PATH.search(token) for token in tokens):
        return ENV_FILE_REASON
    if _FORCE_PUSH.search(command):
        return FORCE_PUSH_REASON
    if (
        _NO_VERIFY.search(command)
        or _COMMIT_NO_VERIFY.search(command)
        or _HOOKS_PATH.search(command)
        or _SKIP_HOOKS.search(command)
    ):
        return NO_VERIFY_REASON
    return None
