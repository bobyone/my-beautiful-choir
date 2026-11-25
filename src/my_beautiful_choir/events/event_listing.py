# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Event listing value object."""

from dataclasses import dataclass

from my_beautiful_choir.choirs.choir import Choir
from my_beautiful_choir.events.period import Period
from my_beautiful_choir.events.visible_event import VisibleEvent


@dataclass(frozen=True)
class EventListing:
    """The events of a choir an observer may see over a period, sorted by start."""

    choir: Choir
    period: Period
    events: tuple[VisibleEvent, ...]
