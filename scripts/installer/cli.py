# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Command-line entry point shared by the desktop installers."""

import argparse
import logging
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from scripts.installer.client import ClientRegistration
from scripts.installer.errors import InstallationError
from scripts.installer.installer import install

_LOGGER = logging.getLogger(__name__)


def main(
    client_name: str,
    client_factory: Callable[[Mapping[str, str]], ClientRegistration],
    argv: Sequence[str] | None = None,
) -> int:
    """Install personal mode for the given client and report how to connect."""
    parser = argparse.ArgumentParser(description=f"Install my-beautiful-choir for {client_name}.")
    parser.add_argument(
        "--node-dir", type=Path, help="Directory with the installed Node.js and npm executables."
    )
    parser.add_argument(
        "--replace", action="store_true", help="Replace an existing conflicting registration."
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    def confirm_replace() -> bool:
        if args.replace:
            return True
        if not sys.stdin.isatty():
            return False
        try:
            return input(
                f"Replace the existing my-beautiful-choir registration in {client_name}? [y/N] "
            ).strip().casefold() in {"y", "yes"}
        except EOFError:
            return False

    try:
        environment = dict(os.environ)
        client = client_factory(environment)
        install(
            Path(__file__).resolve().parents[2],
            client,
            confirm_replace,
            environment,
            node_dir=args.node_dir,
        )
    except InstallationError as error:
        _LOGGER.error("%s", error)
        return 1
    except KeyboardInterrupt:
        _LOGGER.info("Installation cancelled.")
        return 130
    _LOGGER.info(
        "Restart %s, then ask for information about my-beautiful-choir.",
        client_name,
    )
    return 0
