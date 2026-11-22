# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Rules of the attributes of a work."""

import re
import unicodedata
from dataclasses import replace

from my_beautiful_choir.repertoire.errors import InvalidWorkError
from my_beautiful_choir.repertoire.work import WorkChanges, WorkDetails

TITLE_LENGTH = 200
NAME_LENGTH = 200
VOICING_LENGTH = 50
NOTES_LENGTH = 2000
MAXIMUM_LANGUAGES = 10

_LANGUAGE_CODE = re.compile(r"^[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*$")


def _text(attribute: str, value: str | None, maximum: int) -> str | None:
    """Trimmed text in Unicode normal form C; empty becomes None."""
    if value is None:
        return None
    cleaned = unicodedata.normalize("NFC", value.strip())
    if len(cleaned) > maximum:
        raise InvalidWorkError(attribute, f"at most {maximum} characters")
    return cleaned or None


def _language(code: str) -> str:
    """Canonical case of a BCP 47 code: ``fr``, ``sr-Latn``, ``pt-BR``."""
    code = code.strip()
    if not _LANGUAGE_CODE.match(code):
        raise InvalidWorkError("sung language", f"{code!r} is not a BCP 47 language code")
    first, *others = code.split("-")
    parts = [first.lower()]
    for part in others:
        if len(part) == 4 and part.isalpha():
            parts.append(part.title())
        elif len(part) == 2 or part.isdigit():
            parts.append(part.upper())
        else:
            parts.append(part.lower())
    return "-".join(parts)


def _languages(codes: tuple[str, ...]) -> tuple[str, ...]:
    canonical = tuple(dict.fromkeys(_language(code) for code in codes))
    if len(canonical) > MAXIMUM_LANGUAGES:
        raise InvalidWorkError("sung language", f"at most {MAXIMUM_LANGUAGES} languages")
    return canonical


def clean_work_details(details: WorkDetails) -> WorkDetails:
    """Validated and normalized details.

    Raises:
        InvalidWorkError: if the title is empty or an attribute is too long or invalid.
    """
    title = _text("title", details.title, TITLE_LENGTH)
    if title is None:
        raise InvalidWorkError("title", "it must not be empty")
    return WorkDetails(
        title=title,
        composer=_text("composer", details.composer, NAME_LENGTH),
        arranger=_text("arranger", details.arranger, NAME_LENGTH),
        voicing=_text("voicing", details.voicing, VOICING_LENGTH),
        sung_languages=_languages(details.sung_languages),
        notes=_text("notes", details.notes, NOTES_LENGTH),
    )


def apply_work_changes(details: WorkDetails, changes: WorkChanges) -> WorkDetails:
    """Details with the changes applied, validated and normalized.

    Raises:
        InvalidWorkError: as ``clean_work_details``.
    """
    updated = replace(
        details,
        **{
            name: getattr(changes, name)
            for name in ("title", "composer", "arranger", "voicing", "sung_languages", "notes")
            if getattr(changes, name) is not None
        },
    )
    return clean_work_details(updated)


def search_text(text: str | None) -> str | None:
    """Text compared when searching: case-folded, without accents."""
    if text is None:
        return None
    decomposed = unicodedata.normalize("NFKD", text.strip().casefold())
    return "".join(c for c in decomposed if not unicodedata.combining(c))
