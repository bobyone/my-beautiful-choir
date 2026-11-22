# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Adapt Claude Code and Codex pre-tool requests to the shared protection rules."""

import json
import re
import sys

from tools.assistant_hooks.protection_rules import (
    FILE_TOOLS,
    PATH_KEYS,
    SHELL_TOOLS,
    check_command,
    check_path,
)

MALFORMED_REQUEST = (
    "The hook could not evaluate this request. Retry with an explicit command or path."
)
PATCH_HEADER = re.compile(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$")
PATCH_PREAMBLE = "*** Begin Patch"
PATCH_END = "*** End Patch"


def check_request(payload: object) -> str | None:
    """Return a refusal reason for a protected request, or allow it to proceed."""
    if not isinstance(payload, dict):
        return MALFORMED_REQUEST
    tool_name = payload.get("tool_name")
    if not isinstance(tool_name, str) or not tool_name:
        return MALFORMED_REQUEST
    if tool_name not in FILE_TOOLS and tool_name not in SHELL_TOOLS and tool_name != "apply_patch":
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return MALFORMED_REQUEST
    if tool_name in FILE_TOOLS:
        paths = [tool_input[key] for key in PATH_KEYS if key in tool_input]
        if not paths or any(not isinstance(path, str) or not path.strip() for path in paths):
            return MALFORMED_REQUEST
        return next((reason for path in paths if (reason := check_path(path))), None)
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return MALFORMED_REQUEST
    if tool_name in SHELL_TOOLS:
        return check_command(command)
    return _check_patch(command)


def _check_patch(patch: str) -> str | None:
    lines = patch.strip().splitlines()
    if lines[0] != PATCH_PREAMBLE or lines[-1] != PATCH_END:
        return MALFORMED_REQUEST
    paths = [match.group(1) for line in lines if (match := PATCH_HEADER.fullmatch(line))]
    if not paths or any(not path.strip() for path in paths):
        return MALFORMED_REQUEST
    return next((reason for path in paths if (reason := check_path(path))), None)


def main() -> int:
    """Read a request from stdin and report any refusal without echoing its input."""
    try:
        reason = check_request(json.load(sys.stdin))
    except (UnicodeError, json.JSONDecodeError):
        reason = MALFORMED_REQUEST
    if reason is None:
        return 0
    sys.stderr.write(f"Blocked by project rules: {reason}\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
