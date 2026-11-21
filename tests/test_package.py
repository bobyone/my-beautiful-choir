# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the package metadata."""

from importlib.metadata import version

import my_beautiful_choir


def test_version_matches_distribution_metadata() -> None:
    assert my_beautiful_choir.__version__ == version("my-beautiful-choir")
