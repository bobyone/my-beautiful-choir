# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the default behaviour of the tool abstraction."""

from my_beautiful_choir.tools.tool import EMPTY_INPUT_SCHEMA
from tests.doubles import StubTool


def test_defaults_to_no_argument_and_no_view() -> None:
    tool = StubTool()
    assert tool.input_schema == EMPTY_INPUT_SCHEMA
    assert tool.view is None
