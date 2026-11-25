# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Integration tests of concurrent event changes on a temporary SQLite file."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import anyio
import pytest

from my_beautiful_choir.authorization.local.local_observer_source import LocalObserverSource
from my_beautiful_choir.authorization.local.local_user_authorization import LocalUserAuthorization
from my_beautiful_choir.choirs.choir import Choir
from my_beautiful_choir.configuration.event_settings import EventSettings
from my_beautiful_choir.events.event import EventChanges, EventDetails
from my_beautiful_choir.events.event_kind import EventKind
from my_beautiful_choir.events.event_service import EventService
from my_beautiful_choir.events.programme_item import ProgrammeItem
from my_beautiful_choir.persistence.sql.sql_database import SqlDatabase
from tests.doubles import FakeClock

NOW = datetime(2026, 11, 25, 12, tzinfo=UTC)


@pytest.mark.anyio
async def test_concurrent_edit_and_hide_keep_both_changes(tmp_path: Path) -> None:
    database = SqlDatabase.in_directory(tmp_path)
    await database.migrate()
    async with database.unit_of_work() as unit_of_work:
        await unit_of_work.choirs.add(Choir(uuid4(), "Chœur", NOW, is_default=True))
        await unit_of_work.commit()
    service = EventService(
        database.unit_of_work,
        FakeClock(NOW),
        LocalUserAuthorization(),
        LocalObserverSource(),
        EventSettings(),
    )
    _, event = await service.create_event(
        None,
        EventKind.CONCERT,
        EventDetails("Concert", NOW),
        [ProgrammeItem(None, "Interval")],
    )

    async with anyio.create_task_group() as group:
        for _ in range(5):
            group.start_soon(service.edit_event, event.id, EventChanges(place="Church"))
            group.start_soon(service.set_programme_hidden, event.id, True)

    _, visible = await service.get_event(event.id)
    assert visible.event.details.place == "Church"
    assert visible.event.programme_hidden
    assert [entry.note for entry in visible.event.programme] == ["Interval"]
