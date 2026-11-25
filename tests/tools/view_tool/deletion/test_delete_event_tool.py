# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the deletion of events, and of the events counted by other deletions."""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from my_beautiful_choir.authorization.observer import PUBLIC
from my_beautiful_choir.confirmation.confirmation_outcome import ConfirmationOutcome
from my_beautiful_choir.confirmation.memory.in_memory_pending_confirmations import (
    InMemoryPendingConfirmations,
)
from my_beautiful_choir.deletion.deletion import DeletionTarget
from my_beautiful_choir.deletion.deletion_preview import DeletionPreview
from my_beautiful_choir.deletion.stale_confirmation_error import StaleConfirmationError
from my_beautiful_choir.events.errors import EventNotFoundError
from my_beautiful_choir.events.event import EventChanges
from my_beautiful_choir.events.event_kind import EventKind
from my_beautiful_choir.tools.view_tool.deletion.confirm_deletion_tool import (
    ConfirmDeletionArguments,
    ConfirmDeletionTool,
)
from my_beautiful_choir.tools.view_tool.deletion.delete_choir_tool import (
    DeleteChoirArguments,
    DeleteChoirTool,
)
from my_beautiful_choir.tools.view_tool.deletion.delete_event_tool import (
    DeleteEventArguments,
    DeleteEventTool,
)
from my_beautiful_choir.tools.view_tool.deletion.delete_work_tool import (
    DeleteWorkArguments,
    DeleteWorkTool,
)
from my_beautiful_choir.tools.view_tool.deletion.deletion_data import deletion_from_data
from tests.doubles import StubConfirmation, StubObserverSource, StubView, tool_context
from tests.repertoire_world import RepertoireWorld

VIEW = StubView(uri="ui://my-beautiful-choir/deletion.html")
STARTS = datetime(2026, 12, 20, 19, 30, tzinfo=UTC)


class _Tools:
    def __init__(self, world: RepertoireWorld) -> None:
        self.world = world
        self.pending = InMemoryPendingConfirmations[DeletionPreview](world.clock)
        conversation = InMemoryPendingConfirmations[tuple[str, DeletionPreview]](world.clock)
        self.event = DeleteEventTool(VIEW, world.events(), self.pending, conversation)
        self.work = DeleteWorkTool(VIEW, world.repertoire(), self.pending, conversation)
        self.choir = DeleteChoirTool(VIEW, world.choirs(), self.pending, conversation)
        self.confirm = ConfirmDeletionTool(
            VIEW, [world.choirs(), world.repertoire(), world.events()], self.pending
        )


@pytest.fixture
async def tools() -> _Tools:
    world = RepertoireWorld()
    await world.choir("Chœur")
    work = await world.work("Chœur", "Ave Maria")
    await world.event("Chœur", "Christmas concert", STARTS, works=[work, work])
    await world.event("Chœur", "Rehearsal", STARTS, EventKind.REHEARSAL)
    return _Tools(world)


def _event_id(tools: _Tools, title: str = "Christmas concert") -> UUID:
    return next(e.id for e in tools.world.database.data.events.values() if e.title == title)


@pytest.mark.anyio
async def test_a_confirmed_event_deletion_is_done(tools: _Tools) -> None:
    confirmation = StubConfirmation(ConfirmationOutcome.CONFIRMED)

    result = await tools.event.execute(
        DeleteEventArguments(event_id=_event_id(tools)), tool_context(confirmation)
    )

    label = (
        'the concert "Christmas concert" starting 2026-12-20T19:30:00+00:00 of the choir '
        '"Chœur" with its 2 programme entries'
    )
    assert confirmation.questions == [f"Delete {label}? This cannot be undone."]
    assert result.text == f"Deleted {label}."
    assert result.structured is not None
    deletion = deletion_from_data(result.structured)
    assert deletion.target is DeletionTarget.EVENT
    assert deletion.event_kind is EventKind.CONCERT
    assert deletion.starts_at == STARTS
    assert deletion.programme_entry_count == 2
    assert [e.title for e in tools.world.database.data.events.values()] == ["Rehearsal"]


@pytest.mark.anyio
async def test_the_view_confirms_an_event_deletion(tools: _Tools) -> None:
    pending = await tools.event.execute(
        DeleteEventArguments(event_id=_event_id(tools, "Rehearsal")),
        tool_context(StubConfirmation(ConfirmationOutcome.UNAVAILABLE)),
    )
    assert pending.structured is not None
    token = str(pending.structured["token"])

    result = await tools.confirm.execute(ConfirmDeletionArguments(token=token), tool_context())

    assert result.text == (
        'Deleted the rehearsal "Rehearsal" starting 2026-12-20T19:30:00+00:00 of the choir "Chœur".'
    )


@pytest.mark.anyio
async def test_a_changed_event_cannot_be_deleted_from_a_stale_preview(tools: _Tools) -> None:
    service = tools.world.events()
    event_id = _event_id(tools)
    preview = await service.describe_deletion(event_id)
    await service.edit_event(event_id, EventChanges(title="Gala"))

    with pytest.raises(StaleConfirmationError) as raised:
        await service.delete(preview)

    assert raised.value.preview.deletion.name == "Gala"


@pytest.mark.anyio
async def test_an_event_hidden_from_the_observer_cannot_be_deleted(tools: _Tools) -> None:
    public = tools.world.events(observers=StubObserverSource(PUBLIC))

    with pytest.raises(EventNotFoundError):
        await public.describe_deletion(_event_id(tools, "Rehearsal"))


@pytest.mark.anyio
async def test_deleting_a_work_tells_the_events_whose_programme_includes_it(
    tools: _Tools,
) -> None:
    [work_id] = tools.world.database.data.works
    confirmation = StubConfirmation(ConfirmationOutcome.CONFIRMED)

    result = await tools.work.execute(
        DeleteWorkArguments(work_id=work_id), tool_context(confirmation)
    )

    assert confirmation.questions == [
        'Delete the work "Ave Maria" of the choir "Chœur", which stays without a link in the '
        "programme of 1 event? This cannot be undone."
    ]
    assert result.structured is not None
    assert deletion_from_data(result.structured).event_count == 1
    [concert] = [e for e in tools.world.database.data.events.values() if e.programme]
    assert [entry.work_id for entry in concert.programme] == [None, None]
    assert [entry.work_title for entry in concert.programme] == ["Ave Maria", "Ave Maria"]


@pytest.mark.anyio
async def test_deleting_a_choir_counts_its_events(tools: _Tools) -> None:
    confirmation = StubConfirmation(ConfirmationOutcome.CONFIRMED)

    await tools.choir.execute(DeleteChoirArguments(choir="chœur"), tool_context(confirmation))

    assert confirmation.questions == [
        'Delete the choir "Chœur" with its 1 work and 2 events? This cannot be undone.'
    ]
    assert tools.world.database.data.events == {}


@pytest.mark.anyio
async def test_replacing_an_event_requires_a_fresh_choir_confirmation(tools: _Tools) -> None:
    choirs = tools.world.choirs()
    [choir_id] = tools.world.database.data.choirs
    preview = await choirs.describe_deletion(choir_id)
    events = tools.world.events()
    await events.delete(await events.describe_deletion(_event_id(tools, "Rehearsal")))
    await tools.world.event("Chœur", "New rehearsal", STARTS, EventKind.REHEARSAL)

    with pytest.raises(StaleConfirmationError) as raised:
        await choirs.delete(preview)

    assert raised.value.preview.deletion.event_count == preview.deletion.event_count
    assert raised.value.preview.events != preview.events
    assert tools.world.database.data.choirs


@pytest.mark.anyio
async def test_name_description_and_view(tools: _Tools) -> None:
    assert tools.event.name == "delete_event"
    assert "never ask for it in the conversation" in tools.event.description
    assert tools.event.arguments_model is DeleteEventArguments
    assert tools.event.view is VIEW
    assert not tools.event.app_only
