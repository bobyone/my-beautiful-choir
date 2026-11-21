# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the web mode settings."""

import pytest
from pydantic import ValidationError

from my_beautiful_choir.configuration.web_settings import WebSettings


def test_allowed_hosts_from_comma_separated_text() -> None:
    assert WebSettings(allowed_hosts="a:1,b:2").allowed_hosts == ("a:1", "b:2")  # type: ignore[arg-type]


def test_allowed_hosts_from_sequence() -> None:
    assert WebSettings(allowed_hosts=("a:1",)).allowed_hosts == ("a:1",)


def test_empty_host_is_rejected() -> None:
    with pytest.raises(ValidationError):
        WebSettings(host="")
