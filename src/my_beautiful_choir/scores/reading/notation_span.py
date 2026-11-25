# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""A musical indication with endpoints in a part."""

from dataclasses import dataclass

from my_beautiful_choir.scores.reading.event_location import EventLocation


@dataclass(frozen=True)
class NotationSpan:
    """An indication may begin or end outside the available music."""

    kind: str
    start: EventLocation | None = None
    end: EventLocation | None = None
