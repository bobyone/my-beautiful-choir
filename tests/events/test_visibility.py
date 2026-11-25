# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the visibility rule of the events: every kind for every observer."""

from uuid import uuid4

import pytest

from my_beautiful_choir.authorization.observer import LOCAL_USER, PUBLIC, Observer
from my_beautiful_choir.authorization.observer_kind import ObserverKind
from my_beautiful_choir.events.event import Event
from my_beautiful_choir.events.event_kind import EventKind
from my_beautiful_choir.events.visibility import visible_event
from tests.event_samples import make_event

PARTICIPANT = uuid4()
MANAGER = Observer(ObserverKind.MANAGER, uuid4())
ADMINISTRATOR = Observer(ObserverKind.INSTANCE_ADMINISTRATOR)
CHORISTER = Observer(ObserverKind.CHORISTER, uuid4())
PARTICIPATING_CHORISTER = Observer(ObserverKind.CHORISTER, PARTICIPANT)
CHORISTER_WITHOUT_MEMBER = Observer(ObserverKind.CHORISTER)


def _event(kind: EventKind, *, hidden: bool = False) -> Event:
    return make_event(
        kind,
        programme_hidden=hidden,
        participant_ids=(PARTICIPANT,) if kind is EventKind.LESSON else (),
    )


@pytest.mark.parametrize("observer", [LOCAL_USER, MANAGER, ADMINISTRATOR])
@pytest.mark.parametrize("kind", list(EventKind))
@pytest.mark.parametrize("hidden", [False, True])
def test_local_user_managers_and_administrator_see_everything(
    observer: Observer, kind: EventKind, hidden: bool
) -> None:
    event = _event(kind, hidden=hidden and kind is EventKind.CONCERT)

    visible = visible_event(event, observer)

    assert visible is not None
    assert visible.event == event
    assert visible.complete
    assert not visible.programme_withheld


@pytest.mark.parametrize("hidden", [False, True])
@pytest.mark.parametrize("kind", [EventKind.CONCERT, EventKind.REHEARSAL])
def test_choristers_see_concerts_and_rehearsals_whole(kind: EventKind, hidden: bool) -> None:
    event = _event(kind, hidden=hidden and kind is EventKind.CONCERT)

    visible = visible_event(event, CHORISTER)

    assert visible is not None
    assert visible.event == event
    assert visible.complete


def test_a_participating_chorister_sees_the_lesson_whole() -> None:
    event = _event(EventKind.LESSON)

    visible = visible_event(event, PARTICIPATING_CHORISTER)

    assert visible is not None
    assert visible.event == event


@pytest.mark.parametrize("observer", [CHORISTER, CHORISTER_WITHOUT_MEMBER, PUBLIC])
def test_a_lesson_is_hidden_from_other_choristers_and_the_public(observer: Observer) -> None:
    assert visible_event(_event(EventKind.LESSON), observer) is None


def test_a_rehearsal_is_hidden_from_the_public() -> None:
    assert visible_event(_event(EventKind.REHEARSAL), PUBLIC) is None


def test_the_public_sees_a_concert_without_its_notes() -> None:
    event = _event(EventKind.CONCERT)

    visible = visible_event(event, PUBLIC)

    assert visible is not None
    assert visible.event.details.notes is None
    assert visible.event.programme == event.programme
    assert visible.event.title == event.title
    assert visible.event.details.place == event.details.place
    assert not visible.complete
    assert not visible.programme_withheld


def test_the_public_never_sees_a_hidden_programme() -> None:
    event = _event(EventKind.CONCERT, hidden=True)

    visible = visible_event(event, PUBLIC)

    assert visible is not None
    assert visible.event.programme == ()
    assert visible.event.details.notes is None
    assert visible.programme_withheld
