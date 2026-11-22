# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Structured content and descriptions shared by the work tools."""

from collections.abc import Mapping

from my_beautiful_choir.repertoire.work import Work

SUNG_LANGUAGES_DESCRIPTION = (
    "BCP 47 codes of the languages in which the work is sung, for example ['la'] or ['fr', 'en']."
)
VOICING_DESCRIPTION = "Distribution of voices the work is written for, for example SATB or SSA."


def work_data(work: Work) -> Mapping[str, object]:
    """Structured content describing a work."""
    details = work.details
    return {
        "id": str(work.id),
        "title": details.title,
        "composer": details.composer,
        "arranger": details.arranger,
        "voicing": details.voicing,
        "sung_languages": list(details.sung_languages),
        "notes": details.notes,
        "created_at": work.created_at.isoformat(),
        "updated_at": work.updated_at.isoformat(),
    }


def work_label(work: Work) -> str:
    """Title of the work, with its composer when known."""
    composer = work.details.composer
    return f"{work.title} ({composer})" if composer else work.title
