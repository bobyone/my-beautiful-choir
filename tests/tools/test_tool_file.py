# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the files attached to tool results."""

from my_beautiful_choir.tools.tool_file import ToolFile
from my_beautiful_choir.tools.tool_result import ToolResult


def test_a_result_has_no_file_by_default() -> None:
    assert ToolResult(text="done").files == ()


def test_the_content_of_a_file_stays_out_of_its_representation() -> None:
    file = ToolFile("Alto.pdf", "application/pdf", b"%PDF-secret")
    assert "secret" not in repr(file)
    assert "Alto.pdf" in repr(file)
