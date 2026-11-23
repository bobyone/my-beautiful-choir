# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the score formats."""

import pytest

from my_beautiful_choir.scores.formats.score_format import ScoreFormat


@pytest.mark.parametrize(
    ("score_format", "media_type"),
    [
        (ScoreFormat.PDF, "application/pdf"),
        (ScoreFormat.MUSICXML, "application/vnd.recordare.musicxml+xml"),
        (ScoreFormat.COMPRESSED_MUSICXML, "application/vnd.recordare.musicxml"),
        (ScoreFormat.MUSESCORE, "application/x-musescore"),
    ],
)
def test_media_type(score_format: ScoreFormat, media_type: str) -> None:
    assert score_format.media_type == media_type


def test_every_format_has_a_media_type_and_a_display_name() -> None:
    for score_format in ScoreFormat:
        assert score_format.media_type
        assert score_format.display_name
