# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Check that the Codex catalogue points to the versioned shared skills."""

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_codex_marketplace_points_to_the_shared_plugin() -> None:
    marketplace = json.loads(
        ROOT.joinpath(".agents", "plugins", "marketplace.json").read_text(encoding="utf-8")
    )
    [entry] = marketplace["plugins"]
    assert entry["source"]["source"] == "local"

    source_path = entry["source"]["path"]
    assert source_path.startswith("./")
    plugin_root = (ROOT / source_path).resolve()
    assert plugin_root == ROOT
    manifest = json.loads(plugin_root.joinpath("plugin.json").read_text(encoding="utf-8"))
    assert marketplace["name"] == entry["name"] == manifest["name"]
    assert plugin_root.joinpath("skills", "install", "SKILL.md").is_file()


def test_portable_plugin_version_matches_the_application() -> None:
    python_project = tomllib.loads(ROOT.joinpath("pyproject.toml").read_text(encoding="utf-8"))
    version = re.sub(r"\.dev(\d+)$", r"-dev.\1", python_project["project"]["version"])

    manifest = json.loads(ROOT.joinpath("plugin.json").read_text(encoding="utf-8"))
    assert manifest["version"] == version


def test_claude_plugin_follows_the_main_branch() -> None:
    """Claude Code uses the commit as the version only when none is declared."""
    manifest = json.loads(
        ROOT.joinpath(".claude-plugin", "plugin.json").read_text(encoding="utf-8")
    )
    marketplace = json.loads(
        ROOT.joinpath(".claude-plugin", "marketplace.json").read_text(encoding="utf-8")
    )
    assert "version" not in manifest
    assert all("version" not in entry for entry in marketplace["plugins"])
