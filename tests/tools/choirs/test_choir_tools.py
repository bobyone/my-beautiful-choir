# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the choir tools, with the service on in-memory doubles."""

import pytest

from my_beautiful_choir.authorization.local.local_user_authorization import LocalUserAuthorization
from my_beautiful_choir.choirs.choir_service import ChoirService
from my_beautiful_choir.tools.choirs.create_choir_tool import CreateChoirArguments, CreateChoirTool
from my_beautiful_choir.tools.choirs.list_choirs_tool import ListChoirsTool
from my_beautiful_choir.tools.choirs.rename_choir_tool import RenameChoirArguments, RenameChoirTool
from my_beautiful_choir.tools.choirs.set_default_choir_tool import (
    SetDefaultChoirArguments,
    SetDefaultChoirTool,
)
from my_beautiful_choir.tools.no_arguments import NoArguments
from tests.doubles import FakeClock, tool_context
from tests.persistence_doubles import InMemoryDatabase
from tests.score_doubles import InMemoryFileStorage


@pytest.fixture
def service() -> ChoirService:
    return ChoirService(
        InMemoryDatabase().unit_of_work,
        FakeClock(),
        LocalUserAuthorization(),
        InMemoryFileStorage(),
    )


@pytest.mark.anyio
async def test_list_without_choirs_asks_for_a_first_one(service: ChoirService) -> None:
    result = await ListChoirsTool(service).execute(NoArguments(), tool_context())
    assert "No choir exists yet" in result.text
    assert result.structured == {"choirs": []}


@pytest.mark.anyio
async def test_create_then_list(service: ChoirService) -> None:
    create = CreateChoirTool(service)
    first = await create.execute(CreateChoirArguments(name="Chœur"), tool_context())
    second = await create.execute(CreateChoirArguments(name="Ensemble"), tool_context())
    assert first.text == "The choir Chœur was created. It is the default choir."
    assert second.text == "The choir Ensemble was created."
    assert second.structured == {"choir": {"name": "Ensemble", "is_default": False}}
    listed = await ListChoirsTool(service).execute(NoArguments(), tool_context())
    assert listed.text == "2 choir(s): Chœur (default), Ensemble."


@pytest.mark.anyio
async def test_rename_and_set_default(service: ChoirService) -> None:
    await service.create("Chœur")
    await service.create("Ensemble")
    renamed = await RenameChoirTool(service).execute(
        RenameChoirArguments(choir="ensemble", new_name="Ensemble vocal"), tool_context()
    )
    assert renamed.text == "The choir is now named Ensemble vocal."
    chosen = await SetDefaultChoirTool(service).execute(
        SetDefaultChoirArguments(choir="Ensemble vocal"), tool_context()
    )
    assert chosen.text == "Ensemble vocal is now the default choir."
    assert chosen.structured == {"choir": {"name": "Ensemble vocal", "is_default": True}}


@pytest.mark.parametrize(
    "tool", [ListChoirsTool, CreateChoirTool, RenameChoirTool, SetDefaultChoirTool]
)
def test_tools_describe_themselves(service: ChoirService, tool: type[ListChoirsTool]) -> None:
    instance = tool(service)
    assert instance.name.endswith("choir") or instance.name.endswith("choirs")
    assert instance.description
    assert instance.view is None
    assert instance.arguments_model.model_json_schema()["type"] == "object"
