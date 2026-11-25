# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the deletion tools, with the services on in-memory doubles."""

from uuid import UUID, uuid4

import pytest

from my_beautiful_choir.choirs.errors import ChoirNotFoundError
from my_beautiful_choir.confirmation.confirmation_outcome import ConfirmationOutcome
from my_beautiful_choir.confirmation.errors import ConfirmationExpiredError
from my_beautiful_choir.confirmation.memory.in_memory_pending_confirmations import (
    InMemoryPendingConfirmations,
)
from my_beautiful_choir.deletion.deletion_preview import DeletionPreview
from my_beautiful_choir.repertoire.errors import WorkNotFoundError
from my_beautiful_choir.tools.view_tool.deletion.confirm_deletion_tool import (
    ConfirmDeletionArguments,
    ConfirmDeletionTool,
)
from my_beautiful_choir.tools.view_tool.deletion.delete_choir_tool import (
    DeleteChoirArguments,
    DeleteChoirTool,
)
from my_beautiful_choir.tools.view_tool.deletion.delete_score_tool import (
    DeleteScoreArguments,
    DeleteScoreTool,
)
from my_beautiful_choir.tools.view_tool.deletion.delete_work_tool import (
    DeleteWorkArguments,
    DeleteWorkTool,
)
from my_beautiful_choir.tools.view_tool.deletion.deletion_data import deletion_from_data
from tests.doubles import StubConfirmation, StubView, tool_context
from tests.repertoire_world import RepertoireWorld

VIEW = StubView(uri="ui://my-beautiful-choir/deletion.html")


class _Tools:
    def __init__(self, world: RepertoireWorld) -> None:
        self.world = world
        self.pending = InMemoryPendingConfirmations[DeletionPreview](world.clock)
        conversation = InMemoryPendingConfirmations[tuple[str, DeletionPreview]](world.clock)
        self.choir = DeleteChoirTool(VIEW, world.choirs(), self.pending, conversation)
        self.work = DeleteWorkTool(VIEW, world.repertoire(), self.pending, conversation)
        self.score = DeleteScoreTool(VIEW, world.scores(), self.pending, conversation)
        self.confirm = ConfirmDeletionTool(
            VIEW, [world.choirs(), world.repertoire(), world.scores()], self.pending
        )


@pytest.fixture
async def tools() -> _Tools:
    world = RepertoireWorld()
    await world.choir("Chœur")
    work = await world.work("Chœur", "Ave Maria")
    await world.score(work, "Alto")
    await world.score(work, "Tenor")
    return _Tools(world)


def _work_id(tools: _Tools) -> UUID:
    [work_id] = tools.world.database.data.works
    return work_id


@pytest.mark.anyio
async def test_a_confirmed_deletion_is_done(tools: _Tools) -> None:
    [choir_id] = tools.world.database.data.choirs
    confirmation = StubConfirmation(ConfirmationOutcome.CONFIRMED)
    result = await tools.choir.execute(
        DeleteChoirArguments(choir="chœur"), tool_context(confirmation)
    )
    assert confirmation.questions == [
        'Delete the choir "Chœur" with its 1 work and 2 scores? This cannot be undone.'
    ]
    assert result.text == 'Deleted the choir "Chœur" with its 1 work and 2 scores.'
    assert result.structured["status"] == "deleted"
    assert result.structured["deletion"] == {
        "target": "choir",
        "id": str(choir_id),
        "name": "Chœur",
        "parent_name": None,
        "work_count": 1,
        "score_count": 2,
    }
    assert "token" not in result.structured
    assert tools.world.database.data.choirs == {}
    assert tools.world.storage.files == {}


@pytest.mark.anyio
async def test_a_refused_deletion_deletes_nothing(tools: _Tools) -> None:
    confirmation = StubConfirmation(ConfirmationOutcome.REFUSED)
    result = await tools.work.execute(
        DeleteWorkArguments(work_id=_work_id(tools)), tool_context(confirmation)
    )
    assert confirmation.questions == [
        'Delete the work "Ave Maria" of the choir "Chœur" with its 2 scores? This cannot be undone.'
    ]
    assert result.structured["status"] == "refused"
    assert result.text == (
        'The user refused to delete the work "Ave Maria" of the choir "Chœur" with its '
        "2 scores: nothing was deleted."
    )
    assert len(tools.world.database.data.works) == 1
    assert len(tools.world.storage.files) == 2


@pytest.mark.anyio
async def test_without_elicitation_the_view_confirms_with_a_single_use_token(
    tools: _Tools,
) -> None:
    [score_id, _] = tools.world.database.data.scores
    unavailable = StubConfirmation(ConfirmationOutcome.UNAVAILABLE)
    pending = await tools.score.execute(
        DeleteScoreArguments(score_id=score_id), tool_context(unavailable)
    )
    assert pending.structured["status"] == "pending"
    assert pending.text.startswith(
        'Nothing is deleted yet: the user must confirm the deletion of the score "Alto" '
        '(final v1) of the work "Ave Maria" with the Delete button'
    )
    assert len(tools.world.database.data.scores) == 2
    token = str(pending.structured["token"])

    confirmed = await tools.confirm.execute(ConfirmDeletionArguments(token=token), tool_context())
    assert confirmed.structured["status"] == "deleted"
    assert confirmed.text == 'Deleted the score "Alto" (final v1) of the work "Ave Maria".'
    assert score_id not in tools.world.database.data.scores
    assert len(tools.world.storage.files) == 1

    with pytest.raises(ConfirmationExpiredError):
        await tools.confirm.execute(ConfirmDeletionArguments(token=token), tool_context())


@pytest.mark.anyio
async def test_the_view_confirms_a_choir_and_a_work(tools: _Tools) -> None:
    unavailable = tool_context(StubConfirmation(ConfirmationOutcome.UNAVAILABLE))
    work = await tools.work.execute(DeleteWorkArguments(work_id=_work_id(tools)), unavailable)
    choir = await tools.choir.execute(DeleteChoirArguments(choir="Chœur"), unavailable)
    work_token = ConfirmDeletionArguments(token=str(work.structured["token"]))
    assert (await tools.confirm.execute(work_token, tool_context())).structured[
        "status"
    ] == "deleted"

    choir_token = ConfirmDeletionArguments(token=str(choir.structured["token"]))
    refreshed = await tools.confirm.execute(choir_token, tool_context())
    assert refreshed.structured["status"] == "pending"
    assert deletion_from_data(refreshed.structured).work_count == 0
    assert len(tools.world.database.data.choirs) == 1
    with pytest.raises(ConfirmationExpiredError):
        await tools.confirm.execute(choir_token, tool_context())

    new_token = ConfirmDeletionArguments(token=str(refreshed.structured["token"]))
    assert (await tools.confirm.execute(new_token, tool_context())).structured[
        "status"
    ] == "deleted"
    assert tools.world.database.data.choirs == {}


@pytest.mark.anyio
async def test_an_element_deleted_meanwhile_cannot_be_confirmed(tools: _Tools) -> None:
    unavailable = tool_context(StubConfirmation(ConfirmationOutcome.UNAVAILABLE))
    pending = await tools.work.execute(DeleteWorkArguments(work_id=_work_id(tools)), unavailable)
    await tools.choir.execute(DeleteChoirArguments(choir="Chœur"), tool_context())
    with pytest.raises(WorkNotFoundError):
        await tools.confirm.execute(
            ConfirmDeletionArguments(token=str(pending.structured["token"])), tool_context()
        )


@pytest.mark.anyio
async def test_a_missing_element_asks_nothing(tools: _Tools) -> None:
    confirmation = StubConfirmation()
    with pytest.raises(ChoirNotFoundError):
        await tools.choir.execute(DeleteChoirArguments(choir="Schola"), tool_context(confirmation))
    with pytest.raises(WorkNotFoundError):
        await tools.work.execute(DeleteWorkArguments(work_id=uuid4()), tool_context(confirmation))
    assert confirmation.questions == []


@pytest.mark.anyio
async def test_names_descriptions_and_visibility(tools: _Tools) -> None:
    assert [tools.choir.name, tools.work.name, tools.score.name, tools.confirm.name] == [
        "delete_choir",
        "delete_work",
        "delete_score",
        "confirm_deletion",
    ]
    for tool in (tools.choir, tools.work, tools.score):
        assert "never ask for it in the conversation" in tool.description
        assert not tool.app_only
        assert tool.view is VIEW
    assert "default" in tools.choir.description
    assert tools.confirm.app_only
    assert tools.confirm.view is VIEW
    assert "Deletion view" in tools.confirm.description
    assert tools.choir.arguments_model is DeleteChoirArguments
    assert tools.work.arguments_model is DeleteWorkArguments
    assert tools.score.arguments_model is DeleteScoreArguments
    assert tools.confirm.arguments_model is ConfirmDeletionArguments
