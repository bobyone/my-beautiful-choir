# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Configuration of the structured logs.

Logs are JSON objects, one per line, written to stderr: in personal mode,
stdout carries the MCP protocol and must never receive anything else.
"""

import logging
import sys
from typing import TextIO

from asgi_correlation_id import CorrelationIdFilter
from pythonjsonlogger.json import JsonFormatter

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s %(correlation_id)s"
RENAMED_FIELDS = {"asctime": "timestamp", "levelname": "level", "name": "logger"}

# Loggers of third-party libraries routed through the root handler.
_LIBRARY_LOGGERS = ("uvicorn", "uvicorn.error", "mcp")


def configure_logging(level: str, stream: TextIO | None = None) -> None:
    """Send every log record, as JSON, to ``stream`` (stderr by default).

    Each record carries the correlation id of the HTTP request being served,
    or ``null`` outside a request.
    """
    handler = logging.StreamHandler(stream if stream is not None else sys.stderr)
    handler.setFormatter(JsonFormatter(LOG_FORMAT, rename_fields=RENAMED_FIELDS))
    handler.addFilter(CorrelationIdFilter(default_value=None))

    root = logging.getLogger()
    for existing in list(root.handlers):
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level)

    for name in _LIBRARY_LOGGERS:
        library_logger = logging.getLogger(name)
        library_logger.handlers.clear()
        library_logger.propagate = True
    # The access log of uvicorn holds client IP addresses: it is replaced by
    # the request log of the HTTP transport.
    logging.getLogger("uvicorn.access").disabled = True
