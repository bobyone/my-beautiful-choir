# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Visible event value object."""

from dataclasses import dataclass

from my_beautiful_choir.events.event import Event


@dataclass(frozen=True)
class VisibleEvent:
    """An event as one observer may see it."""

    event: Event
    """The event, without what the observer may not see."""
    complete: bool
    """False when the notes, and possibly the programme, were withheld."""
    programme_withheld: bool = False
    """True when the observer may not see the hidden programme of a concert."""
