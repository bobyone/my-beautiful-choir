# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the rules of the attributes, the programme and the audience of an event."""

from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from my_beautiful_choir.events.errors import InvalidEventError, ProgrammeNotHideableError
from my_beautiful_choir.events.event import EventChanges, EventDetails
from my_beautiful_choir.events.event_kind import EventKind
from my_beautiful_choir.events.event_rules import (
    MAXIMUM_PROGRAMME_ENTRIES,
    apply_event_changes,
    build_programme,
    check_audience,
    clean_event_details,
    clean_programme,
)
from my_beautiful_choir.events.programme_entry import ProgrammeEntry
from my_beautiful_choir.events.programme_item import ProgrammeItem

PARIS = timezone(timedelta(hours=1))
START = datetime(2026, 12, 20, 20, 30, tzinfo=PARIS)


def test_details_are_trimmed_and_dates_converted_to_utc() -> None:
    cleaned = clean_event_details(
        EventDetails(
            title="  Christmas concert ",
            starts_at=START,
            ends_at=START + timedelta(hours=2),
            place=" ",
            notes=" Bring the black folder ",
        )
    )

    assert cleaned == EventDetails(
        title="Christmas concert",
        starts_at=datetime(2026, 12, 20, 19, 30, tzinfo=UTC),
        ends_at=datetime(2026, 12, 20, 21, 30, tzinfo=UTC),
        place=None,
        notes="Bring the black folder",
    )
    assert cleaned.starts_at.tzinfo is UTC


@pytest.mark.parametrize(
    ("details", "attribute"),
    [
        (EventDetails(title=" ", starts_at=START), "title"),
        (EventDetails(title="x" * 201, starts_at=START), "title"),
        (EventDetails(title="Concert", starts_at=START, place="x" * 201), "place"),
        (EventDetails(title="Concert", starts_at=START, notes="x" * 2001), "notes"),
        (EventDetails(title="Concert", starts_at=datetime(2026, 12, 20)), "start"),
        (
            EventDetails(title="Concert", starts_at=START, ends_at=datetime(2026, 12, 21)),
            "end",
        ),
        (
            EventDetails(title="Concert", starts_at=START, ends_at=START - timedelta(minutes=1)),
            "end",
        ),
    ],
)
def test_invalid_details_are_refused(details: EventDetails, attribute: str) -> None:
    with pytest.raises(InvalidEventError) as raised:
        clean_event_details(details)
    assert raised.value.attribute == attribute


def test_dates_out_of_the_supported_range_are_refused() -> None:
    far = datetime.max.replace(tzinfo=timezone(timedelta(hours=-1)))
    with pytest.raises(InvalidEventError, match="outside the supported dates") as raised:
        clean_event_details(EventDetails(title="Concert", starts_at=far))
    assert raised.value.attribute == "start"


def test_notes_are_bounded_by_the_configured_length() -> None:
    details = EventDetails(title="Concert", starts_at=START, notes="x" * 11)
    with pytest.raises(InvalidEventError, match="at most 10 characters"):
        clean_event_details(details, notes_length=10)
    assert clean_event_details(details, notes_length=11).notes == "x" * 11
    with pytest.raises(InvalidEventError, match="at most 10 characters"):
        apply_event_changes(clean_event_details(details), EventChanges(), notes_length=10)


def test_an_event_may_end_when_it_starts() -> None:
    cleaned = clean_event_details(EventDetails(title="Concert", starts_at=START, ends_at=START))
    assert cleaned.ends_at == cleaned.starts_at


def test_changes_keep_omitted_values_and_clear_empty_ones() -> None:
    details = clean_event_details(
        EventDetails(
            title="Concert", starts_at=START, ends_at=START, place="Cathedral", notes="Notes"
        )
    )

    changed = apply_event_changes(details, EventChanges(title="Gala", notes="", clear_end=True))

    assert changed.title == "Gala"
    assert changed.place == "Cathedral"
    assert changed.notes is None
    assert changed.ends_at is None
    assert changed.starts_at == details.starts_at


def test_an_end_cannot_be_given_and_cleared() -> None:
    details = clean_event_details(EventDetails(title="Concert", starts_at=START))
    with pytest.raises(InvalidEventError, match="both given and cleared"):
        apply_event_changes(details, EventChanges(ends_at=START, clear_end=True))


def test_programme_notes_are_normalized() -> None:
    work_id = uuid4()

    cleaned = clean_programme([ProgrammeItem(work_id, " "), ProgrammeItem(None, " Interval ")])

    assert cleaned == (ProgrammeItem(work_id, None), ProgrammeItem(None, "Interval"))


@pytest.mark.parametrize(
    ("items", "reason"),
    [
        ([ProgrammeItem()], "entry 1 needs a work"),
        ([ProgrammeItem(uuid4()), ProgrammeItem(None, "  ")], "entry 2 needs a work"),
        ([ProgrammeItem(None, "x" * 201)], "at most 200 characters"),
        ([ProgrammeItem(uuid4())] * (MAXIMUM_PROGRAMME_ENTRIES + 1), "at most 100 entries"),
    ],
)
def test_invalid_programmes_are_refused(items: list[ProgrammeItem], reason: str) -> None:
    with pytest.raises(InvalidEventError, match=reason):
        clean_programme(items)


def test_a_programme_may_repeat_a_work_and_keeps_its_title() -> None:
    work_id = uuid4()
    items = [ProgrammeItem(work_id), ProgrammeItem(None, "Interval"), ProgrammeItem(work_id, "Bis")]

    programme = build_programme(items, {work_id: "Ave Maria"})

    assert programme == (
        ProgrammeEntry(1, work_id, "Ave Maria", None),
        ProgrammeEntry(2, None, None, "Interval"),
        ProgrammeEntry(3, work_id, "Ave Maria", "Bis"),
    )


def test_only_a_concert_programme_can_be_hidden() -> None:
    assert check_audience(EventKind.CONCERT, True, []) == ()
    with pytest.raises(ProgrammeNotHideableError, match="this event is a rehearsal"):
        check_audience(EventKind.REHEARSAL, True, [])


def test_a_lesson_needs_participants_without_duplicates() -> None:
    member = uuid4()
    assert check_audience(EventKind.LESSON, False, [member, member]) == (member,)
    with pytest.raises(InvalidEventError, match="at least one participant"):
        check_audience(EventKind.LESSON, False, [])


@pytest.mark.parametrize("kind", [EventKind.CONCERT, EventKind.REHEARSAL])
def test_only_a_lesson_has_participants(kind: EventKind) -> None:
    with pytest.raises(InvalidEventError, match="has no participants"):
        check_audience(kind, False, [uuid4()])
