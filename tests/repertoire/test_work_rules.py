# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the rules of the attributes of a work."""

import pytest

from my_beautiful_choir.repertoire.errors import InvalidWorkError
from my_beautiful_choir.repertoire.work import WorkChanges, WorkDetails
from my_beautiful_choir.repertoire.work_rules import (
    apply_work_changes,
    clean_work_details,
    search_text,
    title_matches,
)


def test_details_are_trimmed_and_empty_values_dropped() -> None:
    cleaned = clean_work_details(
        WorkDetails(
            title="  Ave Maria ",
            composer=" Bach ",
            arranger="",
            voicing=" SATB",
            sung_languages=(" la", "LA", "sr-latn", "pt-br"),
            notes="   ",
        )
    )
    assert cleaned == WorkDetails(
        title="Ave Maria",
        composer="Bach",
        arranger=None,
        voicing="SATB",
        sung_languages=("la", "sr-Latn", "pt-BR"),
        notes=None,
    )


@pytest.mark.parametrize(
    ("details", "attribute"),
    [
        (WorkDetails(title=" "), "title"),
        (WorkDetails(title="x" * 201), "title"),
        (WorkDetails(title="x", composer="x" * 201), "composer"),
        (WorkDetails(title="x", arranger="x" * 201), "arranger"),
        (WorkDetails(title="x", voicing="x" * 51), "voicing"),
        (WorkDetails(title="x", notes="x" * 2001), "notes"),
        (WorkDetails(title="x", sung_languages=("latin",)), "sung language"),
        (WorkDetails(title="x", sung_languages=("f",)), "sung language"),
        (
            WorkDetails(title="x", sung_languages=tuple(f"a{c}" for c in "bcdefghijkl")),
            "sung language",
        ),
    ],
)
def test_invalid_details_are_refused(details: WorkDetails, attribute: str) -> None:
    with pytest.raises(InvalidWorkError) as raised:
        clean_work_details(details)
    assert raised.value.attribute == attribute
    assert str(raised.value).startswith(f"The {attribute} of the work is invalid")


def test_changes_keep_none_and_clear_empty_values() -> None:
    details = WorkDetails(
        title="Ave Maria", composer="Bach", voicing="SATB", sung_languages=("la",)
    )
    changed = apply_work_changes(
        details, WorkChanges(composer="", voicing="SSA", sung_languages=())
    )
    assert changed == WorkDetails(title="Ave Maria", voicing="SSA")


def test_search_text_ignores_case_and_accents() -> None:
    assert search_text("  Ave MARÍA à Notre-Dame ") == "ave maria a notre-dame"
    assert search_text("Chœur") == "chœur"
    assert search_text(None) is None


@pytest.mark.parametrize(
    ("title", "matches"),
    [
        ("Adeste fideles (NL15.2)", True),
        ("Adeste fideles, nl15.2.", True),
        ("Adeste fideles NL15.20", False),
        ("Adeste fideles NL15.2.1", False),
        ("Adeste fideles XNL15.2", False),
        ("Adeste fideles 1.NL15.2", False),
    ],
)
def test_reference_requires_the_complete_code(title: str, matches: bool) -> None:
    assert title_matches(title, " NL15.2 ", reference=True) is matches


def test_title_lookup_matches_a_fragment_without_case_or_accents() -> None:
    assert title_matches("Peuple fidèle", " FIDELE ", reference=False)
    assert not title_matches("Peuple fidèle", " ", reference=False)
