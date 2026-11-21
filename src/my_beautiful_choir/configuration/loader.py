# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Loading of the settings from the command line and the environment.

This module is only used by the entry point: no other component reads the
command line or the environment.
"""

import argparse
from collections.abc import Sequence
from typing import Any, NoReturn

from pydantic import ValidationError
from pydantic_core import ErrorDetails

from my_beautiful_choir import __version__
from my_beautiful_choir.configuration.errors import ConfigurationError, ConfigurationIssue
from my_beautiful_choir.configuration.mode import Mode
from my_beautiful_choir.configuration.settings import ENV_NESTED_DELIMITER, ENV_PREFIX, Settings

PROGRAM_NAME = "my-beautiful-choir"


class _ArgumentParser(argparse.ArgumentParser):
    """Argument parser raising ConfigurationError instead of exiting on invalid usage."""

    def error(self, message: str) -> NoReturn:
        raise ConfigurationError((ConfigurationIssue(key="command line", message=message),))


def _build_parser() -> _ArgumentParser:
    parser = _ArgumentParser(
        prog=PROGRAM_NAME,
        description="Choir management application, delivered as an MCP app.",
    )
    parser.add_argument(
        "--mode",
        choices=[mode.value for mode in Mode],
        help="running mode (default: personal, or the MBC_MODE environment variable)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _environment_key(location: tuple[int | str, ...]) -> str:
    return ENV_PREFIX + ENV_NESTED_DELIMITER.join(str(part) for part in location).upper()


def _issue_from(error: ErrorDetails) -> ConfigurationIssue:
    key = _environment_key(tuple(error["loc"]))
    value = error.get("input")
    message = error["msg"]
    if isinstance(value, str | int):
        message = f"{value!r} is not valid: {message}"
    return ConfigurationIssue(key=key, message=message)


def load_settings(argv: Sequence[str]) -> Settings:
    """Parse the command line, read the environment and return the validated settings.

    The ``--mode`` option takes precedence over the ``MBC_MODE`` environment variable.

    Raises:
        ConfigurationError: if the command line or a configuration value is invalid.
    """
    arguments = _build_parser().parse_args(list(argv))
    overrides: dict[str, Any] = {}
    if arguments.mode is not None:
        overrides["mode"] = arguments.mode
    try:
        return Settings(**overrides)
    except ValidationError as error:
        issues = tuple(_issue_from(detail) for detail in error.errors())
        raise ConfigurationError(issues) from error
