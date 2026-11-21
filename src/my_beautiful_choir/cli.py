# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Entry point: reads the configuration, assembles the mode and runs the application."""

import logging
import sys
from collections.abc import Sequence
from typing import TextIO

from my_beautiful_choir import APPLICATION_NAME
from my_beautiful_choir.configuration.errors import ConfigurationError
from my_beautiful_choir.configuration.loader import load_settings
from my_beautiful_choir.containers import container_factory
from my_beautiful_choir.errors import StartupError
from my_beautiful_choir.monitoring.logging_setup import configure_logging

_LOGGER = logging.getLogger(__name__)

TROUBLESHOOTING_URL = (
    "https://github.com/bobyone/my-beautiful-choir/blob/main/docs/how-to/troubleshoot-startup.md"
)
UNEXPECTED_EXIT_CODE = 1
UNEXPECTED_ERROR_CODE = "MBC-UNEXPECTED"


def _report(
    stream: TextIO, error_code: str, message: str, details: Sequence[str], remedy: str
) -> None:
    """Write the human-readable startup failure message."""
    lines = [f"{APPLICATION_NAME} could not start [{error_code}]: {message}"]
    lines += [f"  - {detail}" for detail in details]
    lines += [remedy, f"See {TROUBLESHOOTING_URL}"]
    stream.write("\n".join(lines) + "\n")


def _fail(error: StartupError, stream: TextIO) -> int:
    details: Sequence[str] = ()
    if isinstance(error, ConfigurationError):
        details = [f"{issue.key}: {issue.message}" for issue in error.issues]
    _LOGGER.error(
        "startup_failed",
        extra={"error_code": error.error_code, "exit_code": error.exit_code, "details": details},
    )
    _report(stream, error.error_code, error.message, details, error.remedy)
    return error.exit_code


def main(argv: Sequence[str] | None = None) -> int:
    """Run my-beautiful-choir and return the process exit code.

    Exit codes: 0 normal stop, 1 unexpected error, 2 invalid configuration or
    usage, 3 unavailable resource, 4 incomplete installation, 5 unusable data store.
    """
    configure_logging("INFO")
    try:
        settings = load_settings(sys.argv[1:] if argv is None else argv)
    except ConfigurationError as error:
        return _fail(error, sys.stderr)
    configure_logging(settings.log_level)

    container = container_factory.create_container(settings)
    try:
        container.application().run()
    except StartupError as error:
        return _fail(error, sys.stderr)
    except KeyboardInterrupt:
        _LOGGER.info("Interrupted, stopping")
    except Exception:
        _LOGGER.exception(
            "startup_failed",
            extra={"error_code": UNEXPECTED_ERROR_CODE, "exit_code": UNEXPECTED_EXIT_CODE},
        )
        _report(
            sys.stderr,
            UNEXPECTED_ERROR_CODE,
            "an unexpected error occurred.",
            (),
            "The details are in the log record above; please report the problem.",
        )
        return UNEXPECTED_EXIT_CODE
    return 0
