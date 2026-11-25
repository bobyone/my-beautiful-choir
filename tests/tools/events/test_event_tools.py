# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the event tools, with the services on in-memory doubles."""

from datetime import UTC, datetime, timedelta, timezone
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from my_beautiful_choir.authorization.observer import PUBLIC
from my_beautiful_choir.configuration.event_settings import EventSettings
from my_beautiful_choir.events.errors import EventNotFoundError, InvalidEventError
from my_beautiful_choir.repertoire.work import Work
from my_beautiful_choir.tools.events.create_event_tool import (
    CreateEventArguments,
    CreateEventTool,
)
from my_beautiful_choir.tools.events.edit_event_tool import EditEventArguments, EditEventTool
from my_beautiful_choir.tools.events.event_data import ProgrammeItemArguments
from my_beautiful_choir.tools.events.get_event_tool import GetEventArguments, GetEventTool
from my_beautiful_choir.tools.events.list_events_tool import ListEventsArguments, ListEventsTool
from my_beautiful_choir.tools.events.set_programme_hidden_tool import (
    SetProgrammeHiddenArguments,
    SetProgrammeHiddenTool,
)
from tests.doubles import StubObserverSource, tool_context
from tests.repertoire_world import RepertoireWorld

PARIS = timezone(timedelta(hours=1))
NOW = datetime(2026, 11, 25, 12, tzinfo=UTC)


class _World:
    def __init__(self, world: RepertoireWorld, work: Work) -> None:
        self.world = world
        self.work = work
        self.observers = StubObserverSource()
        service = world.events(observers=self.observers)
        self.create = CreateEventTool(service)
        self.edit = EditEventTool(service)
        self.hide = SetProgrammeHiddenTool(service)
        self.get = GetEventTool(service)
        self.list = ListEventsTool(service, EventSettings())


@pytest.fixture
async def tools() -> _World:
    world = RepertoireWorld()
    await world.choir("Chœur")
    world.clock.current = NOW
    work = await world.work("Chœur", "Ave Maria")
    return _World(world, work)


async def _create_concert(tools: _World) -> UUID:
    result = await tools.create.execute(
        CreateEventArguments(
            kind="concert",
            title="Christmas concert",
            starts_at=datetime(2026, 12, 20, 20, 30, tzinfo=PARIS),
            place="Cathedral",
            notes="Arrive at 19:30",
            programme=[
                ProgrammeItemArguments(work_id=tools.work.id),
                ProgrammeItemArguments(note="Interval"),
            ],
        ),
        tool_context(),
    )
    event = cast(dict[str, Any], result.structured["event"])
    return UUID(event["id"])


@pytest.mark.anyio
async def test_create_then_get_a_concert(tools: _World) -> None:
    event_id = await _create_concert(tools)

    result = await tools.get.execute(GetEventArguments(event_id=event_id), tool_context())

    assert result.text == (
        f'Choir "Chœur": The concert "Christmas concert" starting 2026-12-20T19:30:00+00:00 '
        f"(id {event_id}).\nPlace: Cathedral.\nNotes: Arrive at 19:30\nProgramme:\n"
        "1. Ave Maria\n2. Interval"
    )
    event = cast(dict[str, Any], result.structured["event"])
    assert event["kind"] == "concert"
    assert event["starts_at"] == "2026-12-20T19:30:00+00:00"
    assert event["notes"] == "Arrive at 19:30"
    assert event["programme_hidden"] is False
    assert event["programme"] == [
        {"position": 1, "work_id": str(tools.work.id), "work_title": "Ave Maria", "note": None},
        {"position": 2, "work_id": None, "work_title": None, "note": "Interval"},
    ]


@pytest.mark.anyio
async def test_create_reports_the_event(tools: _World) -> None:
    result = await tools.create.execute(
        CreateEventArguments(
            kind="rehearsal", title="Rehearsal", starts_at=NOW + timedelta(days=1)
        ),
        tool_context(),
    )
    event = cast(dict[str, Any], result.structured["event"])
    assert result.text == (
        f'Added the rehearsal "Rehearsal" starting 2026-11-26T12:00:00+00:00 to the choir '
        f'"Chœur" (id {event["id"]}).'
    )
    assert result.structured["choir"] == "Chœur"


def test_lessons_cannot_be_created_yet() -> None:
    with pytest.raises(ValidationError):
        CreateEventArguments.model_validate(
            {"kind": "lesson", "title": "Lesson", "starts_at": NOW.isoformat()}
        )


@pytest.mark.anyio
async def test_naive_dates_are_refused(tools: _World) -> None:
    with pytest.raises(InvalidEventError, match="time zone offset"):
        await tools.create.execute(
            CreateEventArguments(
                kind="concert",
                title="Concert",
                starts_at=datetime(2026, 12, 20, 20, 30),
            ),
            tool_context(),
        )


@pytest.mark.anyio
async def test_edit_and_hide_the_programme(tools: _World) -> None:
    event_id = await _create_concert(tools)

    edited = await tools.edit.execute(
        EditEventArguments(event_id=event_id, title="Gala", place="", programme=[]),
        tool_context(),
    )
    hidden = await tools.hide.execute(
        SetProgrammeHiddenArguments(event_id=event_id, hidden=True), tool_context()
    )
    shown = await tools.hide.execute(
        SetProgrammeHiddenArguments(event_id=event_id, hidden=False), tool_context()
    )

    assert edited.text == 'Updated the concert "Gala" starting 2026-12-20T19:30:00+00:00.'
    event = cast(dict[str, Any], edited.structured["event"])
    assert event["place"] is None
    assert event["programme"] == []
    assert hidden.text == (
        'The programme of the concert "Gala" starting 2026-12-20T19:30:00+00:00 is hidden '
        "from the public."
    )
    assert "shown to the public" in shown.text


@pytest.mark.anyio
async def test_the_public_sees_neither_notes_nor_a_hidden_programme(tools: _World) -> None:
    event_id = await _create_concert(tools)
    await tools.hide.execute(
        SetProgrammeHiddenArguments(event_id=event_id, hidden=True), tool_context()
    )
    tools.observers.current = PUBLIC

    result = await tools.get.execute(GetEventArguments(event_id=event_id), tool_context())

    assert "Arrive at 19:30" not in result.text
    assert "Ave Maria" not in result.text
    assert "The programme is hidden from the public." in result.text
    event = cast(dict[str, Any], result.structured["event"])
    assert "notes" not in event
    assert "programme_hidden" not in event
    assert event["programme"] == []
    assert event["programme_withheld"] is True


@pytest.mark.anyio
async def test_list_events_of_the_default_period(tools: _World) -> None:
    event_id = await _create_concert(tools)

    result = await tools.list.execute(ListEventsArguments(), tool_context())

    assert result.text == (
        'Events of the choir "Chœur" from 2026-11-25T12:00:00+00:00 to '
        "2027-02-25T12:00:00+00:00:\n"
        f'- the concert "Christmas concert" starting 2026-12-20T19:30:00+00:00 (id {event_id})'
    )
    assert result.structured["period"] == {
        "start": "2026-11-25T12:00:00+00:00",
        "end": "2027-02-25T12:00:00+00:00",
    }
    assert len(cast(list[object], result.structured["events"])) == 1

    empty = await tools.list.execute(
        ListEventsArguments(end=datetime(2026, 1, 1, tzinfo=UTC)), tool_context()
    )
    assert empty.text.startswith('The choir "Chœur" has no event from 2025-10-01')


@pytest.mark.anyio
async def test_an_unknown_event_is_not_found(tools: _World) -> None:
    with pytest.raises(EventNotFoundError):
        await tools.get.execute(GetEventArguments(event_id=uuid4()), tool_context())


@pytest.mark.anyio
async def test_names_and_descriptions(tools: _World) -> None:
    assert [t.name for t in (tools.create, tools.edit, tools.hide, tools.get, tools.list)] == [
        "create_event",
        "edit_event",
        "set_programme_hidden",
        "get_event",
        "list_events",
    ]
    for tool in (tools.create, tools.edit, tools.get, tools.list):
        assert "UTC" in tool.description
    assert "92 days" in tools.list.description
    assert "366 days" in tools.list.description
    assert "Lessons are not available yet" in tools.create.description
    assert "set_programme_hidden" in tools.edit.description
    assert tools.create.arguments_model is CreateEventArguments
    assert tools.edit.arguments_model is EditEventArguments
    assert tools.hide.arguments_model is SetProgrammeHiddenArguments
    assert tools.get.arguments_model is GetEventArguments
    assert tools.list.arguments_model is ListEventsArguments
