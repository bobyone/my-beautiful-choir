# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the show_about tool."""

import pytest

from my_beautiful_choir.application.application_info import ApplicationInfo
from my_beautiful_choir.configuration.mode import Mode
from my_beautiful_choir.tools.view_tool.about.show_about_tool import ShowAboutTool
from tests.doubles import StubView


@pytest.mark.anyio
@pytest.mark.parametrize(("mode", "label"), [(Mode.PERSONAL, "personal"), (Mode.WEB, "web")])
async def test_result_describes_the_application(mode: Mode, label: str) -> None:
    tool = ShowAboutTool(StubView(), ApplicationInfo("my-beautiful-choir", "1.2.3", mode))
    result = await tool.execute({})
    assert result.text == f"my-beautiful-choir 1.2.3, {label} mode."
    assert result.structured == {"name": "my-beautiful-choir", "version": "1.2.3", "mode": label}


def test_is_bound_to_its_view() -> None:
    view = StubView()
    tool = ShowAboutTool(view, ApplicationInfo("my-beautiful-choir", "1.2.3", Mode.WEB))
    assert tool.view is view
    assert tool.name == "show_about"
    assert "version" in tool.description
