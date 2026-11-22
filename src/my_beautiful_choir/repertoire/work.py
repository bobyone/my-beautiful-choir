# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Work value objects."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class WorkDetails:
    """What describes a work, as entered by the user."""

    title: str
    composer: str | None = None
    arranger: str | None = None
    voicing: str | None = None
    """Distribution of voices, for example SATB."""
    sung_languages: tuple[str, ...] = ()
    """BCP 47 language codes, for example ``la`` or ``fr``."""
    notes: str | None = None


@dataclass(frozen=True)
class WorkChanges:
    """Changes of a work: None leaves an attribute unchanged, an empty value clears it."""

    title: str | None = None
    composer: str | None = None
    arranger: str | None = None
    voicing: str | None = None
    sung_languages: tuple[str, ...] | None = None
    notes: str | None = None


@dataclass(frozen=True)
class Work:
    """Musical work of a choir's repertoire."""

    id: UUID
    choir_id: UUID
    details: WorkDetails
    created_at: datetime
    updated_at: datetime

    @property
    def title(self) -> str:
        """Title of the work."""
        return self.details.title
