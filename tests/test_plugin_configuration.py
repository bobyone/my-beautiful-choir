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


def test_plugin_versions_match_the_application() -> None:
    python_project = tomllib.loads(ROOT.joinpath("pyproject.toml").read_text(encoding="utf-8"))
    version = re.sub(r"\.dev(\d+)$", r"-dev.\1", python_project["project"]["version"])

    for path in ("plugin.json", ".claude-plugin/plugin.json"):
        manifest = json.loads(ROOT.joinpath(path).read_text(encoding="utf-8"))
        assert manifest["version"] == version
