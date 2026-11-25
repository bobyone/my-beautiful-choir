# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Operations on the events of a choir (flows A to F of issue #30)."""

from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime
from uuid import UUID, uuid4

from my_beautiful_choir.authorization.authorization import Authorization
from my_beautiful_choir.authorization.observer_source import ObserverSource
from my_beautiful_choir.authorization.permission import Permission
from my_beautiful_choir.choirs.choir import Choir
from my_beautiful_choir.choirs.choir_service import find_choir
from my_beautiful_choir.clock.clock import Clock
from my_beautiful_choir.configuration.event_settings import EventSettings
from my_beautiful_choir.events.errors import EventNotFoundError
from my_beautiful_choir.events.event import Event, EventChanges, EventDetails
from my_beautiful_choir.events.event_kind import EventKind
from my_beautiful_choir.events.event_listing import EventListing
from my_beautiful_choir.events.event_rules import (
    apply_event_changes,
    build_programme,
    check_audience,
    clean_event_details,
    clean_programme,
)
from my_beautiful_choir.events.period import Period
from my_beautiful_choir.events.programme_entry import ProgrammeEntry
from my_beautiful_choir.events.programme_item import ProgrammeItem
from my_beautiful_choir.events.visibility import visible_event
from my_beautiful_choir.events.visible_event import VisibleEvent
from my_beautiful_choir.persistence.unit_of_work import UnitOfWork, UnitOfWorkFactory
from my_beautiful_choir.repertoire.errors import WorkNotFoundError


class EventService:
    """Creates, edits, finds and lists the events of a choir.

    Every event read goes through the visibility rule: an event the current
    observer may not see is reported as not found.
    """

    def __init__(
        self,
        unit_of_work: UnitOfWorkFactory,
        clock: Clock,
        authorization: Authorization,
        observers: ObserverSource,
        settings: EventSettings,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._authorization = authorization
        self._observers = observers
        self._settings = settings

    async def create_event(
        self,
        choir: str | None,
        kind: EventKind,
        details: EventDetails,
        programme: Sequence[ProgrammeItem] = (),
        participant_ids: Sequence[UUID] = (),
    ) -> tuple[Choir, Event]:
        """Add an event to the choir named ``choir``, or to the default choir.

        Raises:
            ChoirNotFoundError, NoChoirError: if the choir cannot be found.
            AccessDeniedError: if the user may not manage its events.
            InvalidEventError: if an attribute, the programme or the audience is invalid.
            WorkNotFoundError: if a programme work is not in the choir's repertoire.
        """
        cleaned = clean_event_details(details)
        items = clean_programme(programme)
        participants = check_audience(kind, False, participant_ids)
        async with self._unit_of_work() as unit_of_work:
            target = await find_choir(unit_of_work.choirs, choir)
            self._authorization.require(Permission.MANAGE_EVENTS, target.id)
            now = self._clock.now()
            event = Event(
                id=uuid4(),
                choir_id=target.id,
                kind=kind,
                details=cleaned,
                created_at=now,
                updated_at=now,
                programme=await _programme(unit_of_work, target.id, items),
                participant_ids=participants,
            )
            await unit_of_work.events.add(event)
            await unit_of_work.commit()
        return target, event

    async def edit_event(
        self,
        event_id: UUID,
        changes: EventChanges,
        programme: Sequence[ProgrammeItem] | None = None,
    ) -> Event:
        """Change the given attributes of an event; a given programme replaces the current one.

        Raises:
            EventNotFoundError: if no event has this id, or the user may not see it.
            AccessDeniedError: if the user may not manage the events of its choir.
            InvalidEventError: if an attribute or the programme is invalid.
            WorkNotFoundError: if a programme work is not in the choir's repertoire.
        """
        items = None if programme is None else clean_programme(programme)
        async with self._unit_of_work() as unit_of_work:
            event = await self._visible(unit_of_work, event_id)
            self._authorization.require(Permission.MANAGE_EVENTS, event.choir_id)
            edited = replace(
                event,
                details=apply_event_changes(event.details, changes),
                updated_at=self._clock.now(),
            )
            if items is not None:
                edited = replace(
                    edited, programme=await _programme(unit_of_work, event.choir_id, items)
                )
            await unit_of_work.events.update(edited)
            await unit_of_work.commit()
        return edited

    async def set_programme_hidden(self, event_id: UUID, hidden: bool) -> Event:
        """Hide the programme of a concert from the public, or show it again.

        Asking for the current state changes nothing.

        Raises:
            EventNotFoundError: if no event has this id, or the user may not see it.
            AccessDeniedError: if the user may not hide programmes in its choir.
            ProgrammeNotHideableError: if the event is not a concert.
        """
        async with self._unit_of_work() as unit_of_work:
            event = await self._visible(unit_of_work, event_id)
            self._authorization.require(Permission.HIDE_PROGRAMME, event.choir_id)
            check_audience(event.kind, hidden, event.participant_ids)
            if event.programme_hidden == hidden:
                return event
            changed = replace(event, programme_hidden=hidden, updated_at=self._clock.now())
            await unit_of_work.events.update(changed)
            await unit_of_work.commit()
        return changed

    async def get_event(self, event_id: UUID) -> tuple[Choir, VisibleEvent]:
        """The event as the current observer may see it, and its choir.

        Raises:
            EventNotFoundError: if no event has this id, or the observer may not see it.
        """
        async with self._unit_of_work() as unit_of_work:
            event = await unit_of_work.events.get(event_id)
            visible = visible_event(event, self._observers.observer(event.choir_id))
            if visible is None:
                raise EventNotFoundError(event_id)
            return await unit_of_work.choirs.get(event.choir_id), visible

    async def list_events(
        self, choir: str | None, start: datetime | None = None, end: datetime | None = None
    ) -> EventListing:
        """Events of the choir (or the default choir) the observer may see over a period.

        Without bounds, the period starts now and lasts the default length.

        Raises:
            ChoirNotFoundError, NoChoirError: if the choir cannot be found.
            InvalidPeriodError: if the period is invalid or too long.
        """
        period = Period.resolve(
            start,
            end,
            now=self._clock.now(),
            default_days=self._settings.default_period_days,
            maximum_days=self._settings.maximum_period_days,
        )
        async with self._unit_of_work() as unit_of_work:
            await unit_of_work.start_snapshot()
            target = await find_choir(unit_of_work.choirs, choir)
            observer = self._observers.observer(target.id)
            events = await unit_of_work.events.list_overlapping(target.id, period)
        visible = (visible_event(event, observer) for event in events)
        return EventListing(target, period, tuple(seen for seen in visible if seen is not None))

    async def _visible(self, unit_of_work: UnitOfWork, event_id: UUID) -> Event:
        """The whole event, once the observer may see it."""
        event = await unit_of_work.events.get(event_id)
        if visible_event(event, self._observers.observer(event.choir_id)) is None:
            raise EventNotFoundError(event_id)
        return event


async def _programme(
    unit_of_work: UnitOfWork, choir_id: UUID, items: Sequence[ProgrammeItem]
) -> tuple[ProgrammeEntry, ...]:
    """Programme entries keeping the titles of works, which must belong to the choir.

    Raises:
        WorkNotFoundError: if a work does not exist or belongs to another choir.
    """
    titles: dict[UUID, str] = {}
    for work_id in {item.work_id for item in items if item.work_id is not None}:
        work = await unit_of_work.works.get(work_id)
        if work.choir_id != choir_id:
            raise WorkNotFoundError(work_id)
        titles[work_id] = work.title
    return build_programme(items, titles)
