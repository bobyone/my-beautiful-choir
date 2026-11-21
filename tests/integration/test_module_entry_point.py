# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Test of ``python -m my_beautiful_choir``."""

import os
import subprocess
import sys

from my_beautiful_choir import __version__


def test_module_runs_the_entry_point() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "my_beautiful_choir", "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout.strip() == f"my-beautiful-choir {__version__}"
