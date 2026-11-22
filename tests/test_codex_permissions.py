# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Regression tests for the Codex workspace deny globs."""

import tomllib
from pathlib import Path, PurePosixPath

import pytest

PROFILE_PATH = Path(__file__).resolve().parents[1] / ".codex" / "config.toml"


@pytest.mark.parametrize(
    ("path", "denied"),
    [
        (".env", True),
        (".env.local", True),
        (".env.production", True),
        (".env.test", True),
        ("deployment/dev/.env.test.local", True),
        ("deployment/dev/.ENV.Production", True),
        (".env.e", True),
        (".env.xample", True),
        (".env.example.local", True),
        (".env.myexample", True),
        (".env.examples", True),
        (".env.", True),
        (".env.example", False),
        (".env.production.example", False),
        ("deployment/dev/.ENV.TEST.Example", False),
        ("deployment/dev/.env.test.local.example", False),
        ("docs/environment.md", False),
    ],
)
def test_workspace_environment_file_denials(path: str, denied: bool) -> None:
    config = tomllib.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    profile = config["permissions"][config["default_permissions"]]
    permissions = profile["filesystem"][":workspace_roots"]
    candidate = PurePosixPath(path)
    is_denied = any(
        candidate.full_match(pattern, case_sensitive=True)
        for pattern, access in permissions.items()
        if access == "deny"
    )
    assert is_denied == denied
