# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Loading of the settings from the command line and the environment.

This module is only used by the entry point: no other component reads the
command line or the environment.
"""

import argparse
import re
from collections.abc import Sequence
from typing import Any, NoReturn

from pydantic import ValidationError
from pydantic_core import ErrorDetails
from pydantic_settings import SettingsError

from my_beautiful_choir import APPLICATION_NAME, __version__
from my_beautiful_choir.configuration.errors import ConfigurationError, ConfigurationIssue
from my_beautiful_choir.configuration.mode import Mode
from my_beautiful_choir.configuration.settings import ENV_NESTED_DELIMITER, ENV_PREFIX, Settings

_UNPARSABLE_FIELD = re.compile(r'field "(\w+)"')


class _ArgumentParser(argparse.ArgumentParser):
    """Argument parser raising ConfigurationError instead of exiting on invalid usage."""

    def error(self, message: str) -> NoReturn:
        raise ConfigurationError((ConfigurationIssue(key="command line", message=message),))


def _build_parser() -> _ArgumentParser:
    parser = _ArgumentParser(
        prog=APPLICATION_NAME,
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


def _issue_from_unparsable(error: SettingsError) -> ConfigurationIssue:
    """Issue for a variable whose value cannot be parsed (a group of keys set as one value)."""
    field = _UNPARSABLE_FIELD.search(str(error))
    key = _environment_key((field.group(1),)) if field else "environment"
    return ConfigurationIssue(
        key=key,
        message="cannot be parsed; set its individual keys instead "
        "(see the configuration reference)",
    )


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
    except SettingsError as error:
        raise ConfigurationError((_issue_from_unparsable(error),)) from error
