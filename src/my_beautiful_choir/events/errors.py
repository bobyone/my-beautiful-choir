# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Exceptions of the events notion."""

from uuid import UUID

from my_beautiful_choir.errors import DomainError
from my_beautiful_choir.events.event_kind import EventKind


class EventError(DomainError):
    """Base class of the errors related to events."""


class EventNotFoundError(EventError):
    """No event has the given id, or the current observer may not see it."""

    def __init__(self, event_id: UUID) -> None:
        super().__init__(
            f"No event has the id {event_id}. List the events to find the id of the event."
        )
        self.event_id = event_id


class InvalidEventError(EventError):
    """An attribute of the event is invalid."""

    def __init__(self, attribute: str, reason: str) -> None:
        super().__init__(f"The {attribute} of the event is invalid: {reason}.")
        self.attribute = attribute
        self.reason = reason


class InvalidPeriodError(EventError):
    """The requested period is invalid or too long."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"The period is invalid: {reason}.")
        self.reason = reason


class ProgrammeNotHideableError(EventError):
    """Only the programme of a concert can be hidden from the public."""

    def __init__(self, kind: EventKind) -> None:
        super().__init__(
            f"Only the programme of a concert can be hidden from the public; "
            f"this event is a {kind.value}."
        )
        self.kind = kind
