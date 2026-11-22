# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Integration test of the installer probe against an actual personal-mode server."""

import sys

import pytest
from scripts.installer.probe import verify_launcher

from my_beautiful_choir.views.packaged.packaged_view import packaged_views_directory


@pytest.mark.anyio
@pytest.mark.skipif(
    not packaged_views_directory().joinpath("about.html").is_file(),
    reason="The interface has not been built (uv run nox -s ui)",
)
async def test_probe_checks_real_stdio_server() -> None:
    await verify_launcher([sys.executable, "-m", "my_beautiful_choir", "--mode", "personal"])
