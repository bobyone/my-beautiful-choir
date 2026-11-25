# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Integration tests of the SQL event repository on a temporary SQLite file."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from my_beautiful_choir.choirs.choir import Choir
from my_beautiful_choir.events.errors import EventNotFoundError
from my_beautiful_choir.events.event import Event
from my_beautiful_choir.events.event_kind import EventKind
from my_beautiful_choir.events.period import Period
from my_beautiful_choir.events.programme_entry import ProgrammeEntry
from my_beautiful_choir.persistence.sql.sql_database import SqlDatabase
from my_beautiful_choir.repertoire.work import Work, WorkDetails
from tests.event_samples import make_event

NOW = datetime(2026, 11, 25, 12, tzinfo=UTC)
CHOIR = Choir(uuid4(), "Chœur", NOW, is_default=True)
OTHER = Choir(uuid4(), "Ensemble", NOW, is_default=False)
WORK = Work(uuid4(), CHOIR.id, WorkDetails(title="Ave Maria"), NOW, NOW)


@pytest.fixture
async def database(tmp_path: Path) -> SqlDatabase:
    database = SqlDatabase.in_directory(tmp_path)
    await database.migrate()
    async with database.unit_of_work() as unit_of_work:
        await unit_of_work.choirs.add(CHOIR)
        await unit_of_work.choirs.add(OTHER)
        await unit_of_work.works.add(WORK)
        await unit_of_work.commit()
    return database


def _event(
    starts_at: datetime,
    ends_at: datetime | None = None,
    *,
    title: str = "Concert",
    choir: Choir = CHOIR,
    kind: EventKind = EventKind.CONCERT,
) -> Event:
    return make_event(
        kind,
        choir_id=choir.id,
        title=title,
        starts_at=starts_at,
        ends_at=ends_at,
        programme=(
            ProgrammeEntry(1, WORK.id, "Ave Maria", None),
            ProgrammeEntry(2, None, None, "Interval"),
            ProgrammeEntry(3, WORK.id, "Ave Maria", "Bis"),
        )
        if choir is CHOIR
        else (),
    )


async def _add(database: SqlDatabase, *events: Event) -> None:
    async with database.unit_of_work() as unit_of_work:
        for event in events:
            await unit_of_work.events.add(event)
        await unit_of_work.commit()


@pytest.mark.anyio
async def test_add_get_update_delete(database: SqlDatabase) -> None:
    event = _event(NOW, NOW + timedelta(hours=2))
    await _add(database, event)

    async with database.unit_of_work() as unit_of_work:
        assert await unit_of_work.events.get(event.id) == event
        edited = replace(
            event,
            details=replace(event.details, title="Gala", notes=None),
            programme=(ProgrammeEntry(1, None, None, "Opening"),),
            programme_hidden=True,
            updated_at=NOW + timedelta(days=1),
        )
        await unit_of_work.events.update(edited)
        await unit_of_work.commit()

    async with database.unit_of_work() as unit_of_work:
        assert await unit_of_work.events.get(event.id) == edited
        await unit_of_work.events.delete(event.id)
        await unit_of_work.commit()

    async with database.unit_of_work() as unit_of_work:
        with pytest.raises(EventNotFoundError):
            await unit_of_work.events.get(event.id)


@pytest.mark.anyio
async def test_list_keeps_overlapping_events_sorted(database: SqlDatabase) -> None:
    before = _event(NOW - timedelta(days=1))
    at_start = _event(NOW, title="B")
    spanning = _event(NOW - timedelta(days=2), NOW + timedelta(hours=1), title="Festival")
    same_start = _event(NOW, title="A")
    at_end = _event(NOW + timedelta(days=10))
    after = _event(NOW + timedelta(days=10, seconds=1))
    elsewhere = _event(NOW, choir=OTHER)
    await _add(database, before, at_start, spanning, same_start, at_end, after, elsewhere)

    async with database.unit_of_work() as unit_of_work:
        listed = await unit_of_work.events.list_overlapping(
            CHOIR.id, Period(NOW, NOW + timedelta(days=10))
        )

    assert [event.id for event in listed] == [spanning.id, same_start.id, at_start.id, at_end.id]
    assert listed[0].programme == spanning.programme


@pytest.mark.anyio
async def test_programme_shows_the_current_title_then_the_kept_one(
    database: SqlDatabase,
) -> None:
    event = _event(NOW)
    await _add(database, event)

    async with database.unit_of_work() as unit_of_work:
        await unit_of_work.works.update(
            replace(WORK, details=WorkDetails(title="Ave Maria (Bach)"))
        )
        await unit_of_work.commit()
    async with database.unit_of_work() as unit_of_work:
        renamed = await unit_of_work.events.get(event.id)
        assert renamed.programme[0].work_title == "Ave Maria (Bach)"
        assert await unit_of_work.events.count_referencing_work(WORK.id) == 1
        await unit_of_work.works.delete(WORK.id)
        await unit_of_work.commit()

    async with database.unit_of_work() as unit_of_work:
        kept = await unit_of_work.events.get(event.id)
        assert await unit_of_work.events.count_referencing_work(WORK.id) == 0
    assert kept.programme == (
        ProgrammeEntry(1, None, "Ave Maria", None),
        ProgrammeEntry(2, None, None, "Interval"),
        ProgrammeEntry(3, None, "Ave Maria", "Bis"),
    )


@pytest.mark.anyio
async def test_deleting_a_choir_deletes_its_events(database: SqlDatabase) -> None:
    mine, theirs = _event(NOW), _event(NOW, choir=OTHER)
    await _add(database, mine, theirs)

    async with database.unit_of_work() as unit_of_work:
        assert await unit_of_work.events.count_of_choir(CHOIR.id) == 1
        await unit_of_work.choirs.delete(CHOIR.id)
        await unit_of_work.commit()

    async with database.unit_of_work() as unit_of_work:
        assert await unit_of_work.events.count_of_choir(CHOIR.id) == 0
        with pytest.raises(EventNotFoundError):
            await unit_of_work.events.get(mine.id)
        assert await unit_of_work.events.get(theirs.id) == theirs


@pytest.mark.anyio
async def test_lesson_participants_are_not_stored_yet(database: SqlDatabase) -> None:
    lesson = replace(_event(NOW, kind=EventKind.LESSON), participant_ids=(uuid4(),))
    async with database.unit_of_work() as unit_of_work:
        with pytest.raises(NotImplementedError, match="#31"):
            await unit_of_work.events.add(lesson)
        with pytest.raises(NotImplementedError, match="#31"):
            await unit_of_work.events.update(lesson)


@pytest.mark.anyio
async def test_downgrade_removes_only_the_events(database: SqlDatabase) -> None:
    await _add(database, _event(NOW))

    await database.downgrade("0004")

    async with database.unit_of_work() as unit_of_work:
        assert await unit_of_work.works.get(WORK.id) == WORK
    await database.migrate()
    async with database.unit_of_work() as unit_of_work:
        assert await unit_of_work.events.count_of_choir(CHOIR.id) == 0
