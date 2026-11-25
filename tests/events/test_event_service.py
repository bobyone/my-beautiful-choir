# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the event service, with in-memory doubles."""

from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from my_beautiful_choir.authorization.errors import AccessDeniedError
from my_beautiful_choir.authorization.local.local_user_authorization import LocalUserAuthorization
from my_beautiful_choir.authorization.observer import PUBLIC, Observer
from my_beautiful_choir.authorization.observer_kind import ObserverKind
from my_beautiful_choir.authorization.permission import Permission
from my_beautiful_choir.choirs.choir_service import ChoirService
from my_beautiful_choir.choirs.errors import ChoirNotFoundError
from my_beautiful_choir.configuration.event_settings import EventSettings
from my_beautiful_choir.events.errors import (
    EventNotFoundError,
    InvalidEventError,
    InvalidPeriodError,
    ProgrammeNotHideableError,
)
from my_beautiful_choir.events.event import EventChanges, EventDetails
from my_beautiful_choir.events.event_kind import EventKind
from my_beautiful_choir.events.event_service import EventService
from my_beautiful_choir.events.programme_entry import ProgrammeEntry
from my_beautiful_choir.events.programme_item import ProgrammeItem
from my_beautiful_choir.repertoire.errors import WorkNotFoundError
from my_beautiful_choir.repertoire.repertoire_service import RepertoireService
from my_beautiful_choir.repertoire.work import Work, WorkChanges, WorkDetails
from tests.doubles import DenyingAuthorization, FakeClock, StubObserverSource
from tests.persistence_doubles import InMemoryDatabase
from tests.score_doubles import InMemoryFileStorage

PARIS = timezone(timedelta(hours=1))
CONCERT = EventDetails(
    title="Christmas concert",
    starts_at=datetime(2026, 12, 20, 20, 30, tzinfo=PARIS),
    ends_at=datetime(2026, 12, 20, 22, tzinfo=PARIS),
    place="Cathedral",
    notes="Arrive at 19:30",
)
CHORISTER = Observer(ObserverKind.CHORISTER, uuid4())


@pytest.fixture
def database() -> InMemoryDatabase:
    return InMemoryDatabase()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(datetime(2026, 11, 25, 12, tzinfo=UTC))


@pytest.fixture
def observers() -> StubObserverSource:
    return StubObserverSource()


def _service(
    database: InMemoryDatabase,
    clock: FakeClock,
    observers: StubObserverSource,
    authorization: LocalUserAuthorization | DenyingAuthorization | None = None,
) -> EventService:
    return EventService(
        database.unit_of_work,
        clock,
        authorization or LocalUserAuthorization(),
        observers,
        EventSettings(),
    )


@pytest.fixture
def service(
    database: InMemoryDatabase, clock: FakeClock, observers: StubObserverSource
) -> EventService:
    return _service(database, clock, observers)


@pytest.fixture
def repertoire(database: InMemoryDatabase, clock: FakeClock) -> RepertoireService:
    return RepertoireService(
        database.unit_of_work, clock, LocalUserAuthorization(), InMemoryFileStorage()
    )


@pytest.fixture
async def work(database: InMemoryDatabase, clock: FakeClock, repertoire: RepertoireService) -> Work:
    choirs = ChoirService(
        database.unit_of_work, clock, LocalUserAuthorization(), InMemoryFileStorage()
    )
    await choirs.create("Chœur")
    await choirs.create("Ensemble")
    _, work = await repertoire.add_work(None, WorkDetails(title="Ave Maria"))
    return work


@pytest.mark.anyio
async def test_create_an_event_with_its_programme(service: EventService, work: Work) -> None:
    choir, event = await service.create_event(
        None,
        EventKind.CONCERT,
        CONCERT,
        [ProgrammeItem(work.id), ProgrammeItem(None, "Interval"), ProgrammeItem(work.id, "Bis")],
    )

    assert choir.name == "Chœur"
    assert event.choir_id == choir.id
    assert event.details.starts_at == datetime(2026, 12, 20, 19, 30, tzinfo=UTC)
    assert event.programme == (
        ProgrammeEntry(1, work.id, "Ave Maria", None),
        ProgrammeEntry(2, None, None, "Interval"),
        ProgrammeEntry(3, work.id, "Ave Maria", "Bis"),
    )
    assert not event.programme_hidden
    assert event.created_at == event.updated_at
    _, visible = await service.get_event(event.id)
    assert visible.event == event


@pytest.mark.anyio
async def test_a_work_of_another_choir_cannot_enter_a_programme(
    service: EventService, repertoire: RepertoireService, work: Work
) -> None:
    _, foreign = await repertoire.add_work("Ensemble", WorkDetails(title="Gloria"))

    with pytest.raises(WorkNotFoundError):
        await service.create_event(None, EventKind.CONCERT, CONCERT, [ProgrammeItem(foreign.id)])
    with pytest.raises(WorkNotFoundError):
        await service.create_event(None, EventKind.CONCERT, CONCERT, [ProgrammeItem(uuid4())])


@pytest.mark.anyio
async def test_creation_checks_rights_choir_and_values(
    database: InMemoryDatabase, clock: FakeClock, observers: StubObserverSource, work: Work
) -> None:
    denied = _service(database, clock, observers, DenyingAuthorization(Permission.MANAGE_EVENTS))
    with pytest.raises(AccessDeniedError):
        await denied.create_event(None, EventKind.CONCERT, CONCERT)

    service = _service(database, clock, observers)
    with pytest.raises(ChoirNotFoundError):
        await service.create_event("Unknown", EventKind.CONCERT, CONCERT)
    with pytest.raises(InvalidEventError, match="at least one participant"):
        await service.create_event(None, EventKind.LESSON, CONCERT)
    with pytest.raises(InvalidEventError, match="title"):
        await service.create_event(None, EventKind.REHEARSAL, EventDetails("", CONCERT.starts_at))
    assert database.data.events == {}


@pytest.mark.anyio
async def test_edit_changes_details_and_replaces_the_programme(
    service: EventService, clock: FakeClock, work: Work
) -> None:
    _, event = await service.create_event(
        None, EventKind.CONCERT, CONCERT, [ProgrammeItem(work.id)]
    )
    clock.advance(timedelta(hours=1))

    kept = await service.edit_event(event.id, EventChanges(title="Gala", notes=""))
    assert kept.title == "Gala"
    assert kept.details.notes is None
    assert kept.programme == event.programme
    assert kept.updated_at == clock.now()

    replaced = await service.edit_event(event.id, EventChanges(), [ProgrammeItem(None, "Opening")])
    assert replaced.programme == (ProgrammeEntry(1, None, None, "Opening"),)
    _, visible = await service.get_event(event.id)
    assert visible.event == replaced


@pytest.mark.anyio
async def test_the_programme_shows_the_current_work_title(
    service: EventService, repertoire: RepertoireService, work: Work
) -> None:
    _, event = await service.create_event(
        None, EventKind.CONCERT, CONCERT, [ProgrammeItem(work.id)]
    )
    await repertoire.edit_work(work.id, WorkChanges(title="Ave Maria (Bach)"))

    _, visible = await service.get_event(event.id)

    assert visible.event.programme[0].work_title == "Ave Maria (Bach)"


@pytest.mark.anyio
async def test_hide_and_show_a_concert_programme(
    service: EventService, observers: StubObserverSource, clock: FakeClock, work: Work
) -> None:
    _, event = await service.create_event(
        None, EventKind.CONCERT, CONCERT, [ProgrammeItem(work.id)]
    )
    clock.advance(timedelta(minutes=5))

    hidden = await service.set_programme_hidden(event.id, True)
    again = await service.set_programme_hidden(event.id, True)

    assert hidden.programme_hidden
    assert again == hidden
    observers.current = PUBLIC
    _, public = await service.get_event(event.id)
    assert public.event.programme == ()
    assert public.event.details.notes is None
    assert public.programme_withheld
    observers.current = CHORISTER
    _, chorister = await service.get_event(event.id)
    assert chorister.event.programme == event.programme

    observers.current = Observer(ObserverKind.MANAGER, uuid4())
    shown = await service.set_programme_hidden(event.id, False)
    assert not shown.programme_hidden


@pytest.mark.anyio
async def test_only_a_concert_programme_can_be_hidden(service: EventService, work: Work) -> None:
    _, rehearsal = await service.create_event(None, EventKind.REHEARSAL, CONCERT)

    with pytest.raises(ProgrammeNotHideableError):
        await service.set_programme_hidden(rehearsal.id, True)


@pytest.mark.anyio
async def test_the_instance_administrator_may_hide_but_not_edit(
    database: InMemoryDatabase,
    clock: FakeClock,
    observers: StubObserverSource,
    service: EventService,
    work: Work,
) -> None:
    _, event = await service.create_event(None, EventKind.CONCERT, CONCERT)
    observers.current = Observer(ObserverKind.INSTANCE_ADMINISTRATOR)
    administrator = _service(
        database, clock, observers, DenyingAuthorization(Permission.MANAGE_EVENTS)
    )

    assert (await administrator.set_programme_hidden(event.id, True)).programme_hidden
    with pytest.raises(AccessDeniedError):
        await administrator.edit_event(event.id, EventChanges(title="Gala"))


@pytest.mark.anyio
async def test_events_the_observer_may_not_see_are_not_found(
    database: InMemoryDatabase,
    clock: FakeClock,
    observers: StubObserverSource,
    service: EventService,
    work: Work,
) -> None:
    _, rehearsal = await service.create_event(None, EventKind.REHEARSAL, CONCERT)
    observers.current = PUBLIC
    public = _service(
        database,
        clock,
        observers,
        DenyingAuthorization(Permission.MANAGE_EVENTS, Permission.HIDE_PROGRAMME),
    )

    with pytest.raises(EventNotFoundError):
        await public.get_event(rehearsal.id)
    with pytest.raises(EventNotFoundError):
        await public.edit_event(rehearsal.id, EventChanges(title="Gala"))
    with pytest.raises(EventNotFoundError):
        await public.set_programme_hidden(rehearsal.id, False)
    with pytest.raises(EventNotFoundError):
        await public.get_event(uuid4())


@pytest.mark.anyio
async def test_a_chorister_may_see_but_not_manage(
    database: InMemoryDatabase,
    clock: FakeClock,
    observers: StubObserverSource,
    service: EventService,
    work: Work,
) -> None:
    _, rehearsal = await service.create_event(None, EventKind.REHEARSAL, CONCERT)
    observers.current = CHORISTER
    chorister = _service(
        database,
        clock,
        observers,
        DenyingAuthorization(Permission.MANAGE_EVENTS, Permission.HIDE_PROGRAMME),
    )

    _, visible = await chorister.get_event(rehearsal.id)
    assert visible.event == rehearsal
    with pytest.raises(AccessDeniedError):
        await chorister.edit_event(rehearsal.id, EventChanges(title="Gala"))


@pytest.mark.anyio
async def test_list_the_visible_events_of_a_period(
    service: EventService, observers: StubObserverSource, clock: FakeClock, work: Work
) -> None:
    now = clock.now()
    _, concert = await service.create_event(
        None, EventKind.CONCERT, EventDetails("Concert", now + timedelta(days=2))
    )
    _, rehearsal = await service.create_event(
        None, EventKind.REHEARSAL, EventDetails("Rehearsal", now + timedelta(days=1))
    )
    _, later = await service.create_event(
        None, EventKind.CONCERT, EventDetails("Later", now + timedelta(days=93))
    )
    await service.create_event(
        "Ensemble", EventKind.CONCERT, EventDetails("Elsewhere", now + timedelta(days=1))
    )

    listing = await service.list_events(None)
    assert listing.choir.name == "Chœur"
    assert listing.period.start == now
    assert listing.period.end == now + timedelta(days=92)
    assert [seen.event.id for seen in listing.events] == [rehearsal.id, concert.id]

    observers.current = PUBLIC
    public = await service.list_events(None, now, now + timedelta(days=100))
    assert [seen.event.id for seen in public.events] == [concert.id, later.id]

    with pytest.raises(InvalidPeriodError):
        await service.list_events(None, now, now + timedelta(days=367))
