# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the work tools, with the services on in-memory doubles."""

from uuid import UUID

import pytest

from my_beautiful_choir.authorization.local.local_user_authorization import LocalUserAuthorization
from my_beautiful_choir.choirs.choir_service import ChoirService
from my_beautiful_choir.repertoire.repertoire_service import RepertoireService
from my_beautiful_choir.repertoire.work import WorkDetails
from my_beautiful_choir.tools.repertoire.add_work_tool import AddWorkArguments, AddWorkTool
from my_beautiful_choir.tools.repertoire.edit_work_tool import EditWorkArguments, EditWorkTool
from tests.doubles import FakeClock, tool_context
from tests.persistence_doubles import InMemoryDatabase
from tests.score_doubles import InMemoryFileStorage


@pytest.fixture
async def service() -> RepertoireService:
    database, clock = InMemoryDatabase(), FakeClock()
    await ChoirService(
        database.unit_of_work, clock, LocalUserAuthorization(), InMemoryFileStorage()
    ).create("Chœur")
    return RepertoireService(
        database.unit_of_work, clock, LocalUserAuthorization(), InMemoryFileStorage()
    )


@pytest.mark.anyio
async def test_add_then_edit(service: RepertoireService) -> None:
    added = await AddWorkTool(service).execute(
        AddWorkArguments(title="Ave Maria", composer="Bach", sung_languages=["la"]),
        tool_context(),
    )
    assert added.structured is not None
    work = added.structured["work"]
    assert isinstance(work, dict)
    assert added.text == f"The work Ave Maria (Bach) was added to Chœur; its id is {work['id']}."
    assert work["sung_languages"] == ["la"]
    assert work["created_at"] == "2026-11-21T12:00:00+00:00"

    edited = await EditWorkTool(service).execute(
        EditWorkArguments(work_id=UUID(work["id"]), composer="", voicing="SATB"),
        tool_context(),
    )
    assert edited.text == "The work Ave Maria was updated."
    assert edited.structured is not None
    changed = edited.structured["work"]
    assert isinstance(changed, dict)
    assert (changed["composer"], changed["voicing"], changed["sung_languages"]) == (
        None,
        "SATB",
        ["la"],
    )


@pytest.mark.anyio
async def test_edit_replaces_the_languages(service: RepertoireService) -> None:
    _, work = await service.add_work(None, WorkDetails(title="x", sung_languages=("la",)))
    edited = await EditWorkTool(service).execute(
        EditWorkArguments(work_id=work.id, sung_languages=["fr", "en"]), tool_context()
    )
    assert edited.structured is not None
    changed = edited.structured["work"]
    assert isinstance(changed, dict)
    assert changed["sung_languages"] == ["fr", "en"]


@pytest.mark.anyio
@pytest.mark.parametrize("tool", [AddWorkTool, EditWorkTool])
async def test_tools_describe_themselves(
    service: RepertoireService, tool: type[AddWorkTool]
) -> None:
    instance = tool(service)
    assert instance.name in {"add_work", "edit_work"}
    assert instance.description
    assert instance.view is None
