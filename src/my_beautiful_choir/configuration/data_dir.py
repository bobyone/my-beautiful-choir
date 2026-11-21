# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Default data directory."""

from pathlib import Path

from platformdirs import user_data_path

from my_beautiful_choir import APPLICATION_NAME


def default_data_dir() -> Path:
    """Data directory of the user for my-beautiful-choir, following the platform's conventions."""
    return user_data_path(APPLICATION_NAME, appauthor=False)
