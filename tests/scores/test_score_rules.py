# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the rules of the attributes of a score."""

from uuid import UUID

import pytest

from my_beautiful_choir.scores.errors import InvalidScoreError
from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.score_rules import (
    MAXIMUM_SIZE,
    download_name,
    original_name,
    score_label,
    storage_key,
)


@pytest.mark.parametrize(
    ("original", "score_format", "expected"),
    [
        ("Alto.pdf", ScoreFormat.PDF, "Alto.pdf"),
        ("Alto.PDF", ScoreFormat.PDF, "Alto.pdf"),
        ("Alto", ScoreFormat.PDF, "Alto.pdf"),
        ("Alto.mscz", ScoreFormat.PDF, "Alto.pdf"),
        ("Alto.exe", ScoreFormat.MUSICXML, "Alto.musicxml"),
        ("Gloria.tar.gz", ScoreFormat.COMPRESSED_MUSICXML, "Gloria.tar.mxl"),
        ("Symphony No.5", ScoreFormat.PDF, "Symphony No.5.pdf"),
        ("Op. 3 No. 2", ScoreFormat.PDF, "Op. 3 No. 2.pdf"),
        ('a/b\\c:d*e?f"g<h>i|j.pdf', ScoreFormat.PDF, "a_b_c_d_e_f_g_h_i_j.pdf"),
        ("..hidden.pdf", ScoreFormat.PDF, "hidden.pdf"),
        ("Chœur à 4.mxl", ScoreFormat.COMPRESSED_MUSICXML, "Chœur à 4.mxl"),
        ("CON.pdf", ScoreFormat.PDF, "_CON.pdf"),
        ("nul", ScoreFormat.MUSESCORE, "_nul.mscz"),
    ],
)
def test_download_name(original: str, score_format: ScoreFormat, expected: str) -> None:
    assert download_name(original, "Label", score_format) == expected


def test_download_name_falls_back_on_the_label_then_on_a_generic_name() -> None:
    assert download_name(".pdf", "Alto part", ScoreFormat.PDF) == "Alto part.pdf"
    assert download_name("...", "??", ScoreFormat.PDF) == "__.pdf"
    assert download_name("", " . ", ScoreFormat.PDF) == "score.pdf"


def test_download_name_fits_the_name_length() -> None:
    name = download_name("a" * 300 + ".pdf", "Label", ScoreFormat.MUSESCORE)
    assert len(name) == 255
    assert name.endswith("a.mscz")


def test_the_maximum_size_is_50_megabytes() -> None:
    assert MAXIMUM_SIZE == 50 * 1024 * 1024


@pytest.mark.parametrize(
    ("label", "name", "expected"),
    [
        (" Alto part ", "score.pdf", "Alto part"),
        ("Café", "score.pdf", "Café"),
        (None, "Ave Maria.pdf", "Ave Maria"),
        ("  ", "Ave Maria.v2.mxl", "Ave Maria.v2"),
        (None, "README", "README"),
        (None, ".pdf", ".pdf"),
        (None, "", "PDF"),
        (None, "a" * 300 + ".pdf", "a" * 100),
        ("Alto\x00 part", "score.pdf", "Alto part"),
    ],
)
def test_label(label: str | None, name: str, expected: str) -> None:
    assert score_label(label, name, ScoreFormat.PDF) == expected


def test_a_label_too_long_is_refused() -> None:
    with pytest.raises(InvalidScoreError) as raised:
        score_label("a" * 101, "score.pdf", ScoreFormat.PDF)
    assert raised.value.attribute == "label"
    assert str(raised.value) == "The label of the score is invalid: at most 100 characters."


def test_original_name() -> None:
    assert original_name(" Ave\x07 Maria.pdf ") == "Ave Maria.pdf"
    assert len(original_name("a" * 300)) == 255


def test_storage_key_holds_only_ids() -> None:
    choir_id = UUID("0f8fad5b-d9cb-469f-a165-70867728950e")
    score_id = UUID("7c9e6679-7425-40de-944b-e07fc1f90ae7")
    assert storage_key(choir_id, score_id) == f"choirs/{choir_id}/scores/{score_id}"
