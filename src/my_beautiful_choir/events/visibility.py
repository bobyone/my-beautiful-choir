# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Visibility rule of the events (ADR 0031)."""

from dataclasses import replace

from my_beautiful_choir.authorization.observer import Observer
from my_beautiful_choir.authorization.observer_kind import ObserverKind
from my_beautiful_choir.events.event import Event
from my_beautiful_choir.events.event_kind import EventKind
from my_beautiful_choir.events.visible_event import VisibleEvent

_SEES_EVERYTHING = frozenset(
    {ObserverKind.LOCAL_USER, ObserverKind.MANAGER, ObserverKind.INSTANCE_ADMINISTRATOR}
)


def visible_event(event: Event, observer: Observer) -> VisibleEvent | None:
    """What ``observer`` may see of ``event``, or None if they may not see it.

    ``observer`` is the observer for the choir of the event.

    1. The local user, a manager and the instance administrator see everything.
    2. A concert is seen whole by choristers; the public sees it without its
       notes, and without its programme when it is hidden.
    3. A rehearsal is seen whole by choristers.
    4. A lesson is seen whole by the choristers who are its participants.
    5. Anyone else does not see the event.
    """
    if observer.kind in _SEES_EVERYTHING:
        return VisibleEvent(event, complete=True)
    if observer.kind is ObserverKind.CHORISTER and _chorister_sees(event, observer):
        return VisibleEvent(event, complete=True)
    if observer.kind is ObserverKind.PUBLIC and event.kind is EventKind.CONCERT:
        return _public_concert(event)
    return None


def _chorister_sees(event: Event, observer: Observer) -> bool:
    if event.kind is EventKind.LESSON:
        return observer.member_id is not None and observer.member_id in event.participant_ids
    return True


def _public_concert(event: Event) -> VisibleEvent:
    withheld = event.programme_hidden
    public = replace(
        event,
        details=replace(event.details, notes=None),
        programme=() if withheld else event.programme,
    )
    return VisibleEvent(public, complete=False, programme_withheld=withheld)
