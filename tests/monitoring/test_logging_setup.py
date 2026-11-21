# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the logging configuration."""

import io
import json
import logging
from collections.abc import Iterator

import pytest

from my_beautiful_choir.monitoring.logging_setup import configure_logging


@pytest.fixture(autouse=True)
def _restore_root_logger() -> Iterator[None]:
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    yield
    root.handlers[:] = handlers
    root.setLevel(level)
    logging.getLogger("uvicorn.access").disabled = False


def test_records_are_json_lines_with_correlation_id() -> None:
    stream = io.StringIO()
    configure_logging("INFO", stream)
    logging.getLogger("my_beautiful_choir.test").info("server started", extra={"mode": "web"})
    record = json.loads(stream.getvalue().splitlines()[-1])
    assert record["message"] == "server started"
    assert record["level"] == "INFO"
    assert record["logger"] == "my_beautiful_choir.test"
    assert record["mode"] == "web"
    assert "timestamp" in record
    assert record["correlation_id"] is None


def test_level_filters_records() -> None:
    stream = io.StringIO()
    configure_logging("WARNING", stream)
    logging.getLogger("my_beautiful_choir.test").info("hidden")
    assert stream.getvalue() == ""


def test_library_records_go_through_the_json_handler() -> None:
    stream = io.StringIO()
    configure_logging("INFO", stream)
    logging.getLogger("uvicorn.error").info("listening")
    assert json.loads(stream.getvalue())["logger"] == "uvicorn.error"


def test_uvicorn_access_log_is_disabled() -> None:
    stream = io.StringIO()
    configure_logging("INFO", stream)
    logging.getLogger("uvicorn.access").info("127.0.0.1 GET /")
    assert stream.getvalue() == ""


def test_defaults_to_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO")
    logging.getLogger("my_beautiful_choir.test").info("to stderr")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "to stderr" in captured.err
