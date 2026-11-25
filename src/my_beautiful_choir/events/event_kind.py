# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Kinds of events."""

from enum import StrEnum


class EventKind(StrEnum):
    """Nature of an event, which sets who may see it; it never changes."""

    CONCERT = "concert"
    """Visible to everyone, including the public."""

    REHEARSAL = "rehearsal"
    """Visible to all members of the choir."""

    LESSON = "lesson"
    """Visible to its participants and to the managers."""
