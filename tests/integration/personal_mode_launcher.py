# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Runs the real entry point with views read from a given directory.

Usage: ``python personal_mode_launcher.py <views directory> [options...]``.
Used by the end-to-end tests, before the user interface is built.
"""

import sys
from pathlib import Path

from dependency_injector import providers

from my_beautiful_choir import cli
from my_beautiful_choir.configuration.settings import Settings
from my_beautiful_choir.containers import container_factory
from my_beautiful_choir.containers.application_container import ApplicationContainer

VIEWS = Path(sys.argv[1])
_create_container = container_factory.create_container


def _create_container_with_test_views(settings: Settings) -> ApplicationContainer:
    container = _create_container(settings)
    container.views_directory.override(providers.Object(VIEWS))
    return container


container_factory.create_container = _create_container_with_test_views
raise SystemExit(cli.main(sys.argv[2:]))
