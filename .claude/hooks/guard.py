# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Claude Code PreToolUse hook enforcing the project's critical rules.

It blocks:

- access to environment configuration files and secrets (``.env``,
  ``.env.local``, ``*.pem``, ``*.key``, ``secrets/``), while allowing their
  ``.example`` counterparts;
- forced pushes;
- bypassing Git hooks (``--no-verify``, ``git commit -n``,
  ``core.hooksPath``).

The hook reads the tool call as JSON on stdin and exits with code 2, with the
reason on stderr, to block it.
"""

import json
import re
import sys
from collections.abc import Mapping
from pathlib import PurePath

FILE_TOOLS = frozenset({"Read", "Edit", "MultiEdit", "Write", "NotebookEdit", "Grep", "Glob"})
SHELL_TOOLS = frozenset({"Bash", "PowerShell"})
PATH_KEYS = ("file_path", "notebook_path", "path", "pattern", "glob")

_ENV_FILE = re.compile(r"(?:^|(?<=[\s'\"/\\=<>:(]))\.env(?:\.[\w-]+)*(?![\w])")
_SECRET_PATH = re.compile(r"(?:\.pem|\.key)$|(?:^|[/\\])secrets(?:[/\\]|$)", re.IGNORECASE)
_SEGMENT = r"[^;&|\n]*"
_FORCE_PUSH = re.compile(
    rf"\bgit\b{_SEGMENT}\bpush\b{_SEGMENT}(?:\s--force(?:-with-lease|-if-includes)?\b|\s-[a-zA-Z]*f[a-zA-Z]*\b|\s\+\S)"
)
_NO_VERIFY = re.compile(rf"\bgit\b{_SEGMENT}\s--no-verify\b")
_COMMIT_NO_VERIFY = re.compile(rf"\bgit\b{_SEGMENT}\bcommit\b{_SEGMENT}\s-[a-zA-Z]*n[a-zA-Z]*\b")
_HOOKS_PATH = re.compile(r"core\.hooksPath", re.IGNORECASE)

ENV_FILE_REASON = (
    "Environment configuration files and secrets must never be read: "
    "use the matching .example file instead."
)
FORCE_PUSH_REASON = "Forced pushes require the maintainer's explicit agreement."
NO_VERIFY_REASON = "Git hooks must never be bypassed: fix the failing check instead."


def _mentions_env_file(text: str) -> bool:
    return any(not match.group(0).endswith(".example") for match in _ENV_FILE.finditer(text))


def _is_secret_path(path: str) -> bool:
    name = PurePath(path.replace("\\", "/")).name
    return _mentions_env_file(name) or bool(_SECRET_PATH.search(path))


def find_violation(tool_name: str, tool_input: Mapping[str, object]) -> str | None:
    """Return the reason why the tool call is forbidden, or None when it is allowed."""
    if tool_name in FILE_TOOLS:
        for key in PATH_KEYS:
            value = tool_input.get(key)
            if isinstance(value, str) and _is_secret_path(value):
                return ENV_FILE_REASON
        return None
    if tool_name in SHELL_TOOLS:
        command = tool_input.get("command")
        if not isinstance(command, str):
            return None
        tokens = (token.strip("'\"") for token in command.split())
        if _mentions_env_file(command) or any(_SECRET_PATH.search(token) for token in tokens):
            return ENV_FILE_REASON
        if _FORCE_PUSH.search(command):
            return FORCE_PUSH_REASON
        if (
            _NO_VERIFY.search(command)
            or _COMMIT_NO_VERIFY.search(command)
            or _HOOKS_PATH.search(command)
        ):
            return NO_VERIFY_REASON
    return None


def main() -> int:
    """Read the hook payload from stdin and block the call when it breaks a rule."""
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input")
    reason = find_violation(
        str(payload.get("tool_name", "")),
        tool_input if isinstance(tool_input, dict) else {},
    )
    if reason is None:
        return 0
    sys.stderr.write(f"Blocked by project rules: {reason}\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
