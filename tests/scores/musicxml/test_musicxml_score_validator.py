# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Check structural validation for uncompressed and compressed MusicXML drafts."""

import pytest

from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.musicxml.musicxml_score_validator import MusicXmlScoreValidator
from tests import score_samples


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("format", "content"),
    [
        (ScoreFormat.MUSICXML, score_samples.musicxml()),
        (ScoreFormat.COMPRESSED_MUSICXML, score_samples.compressed_musicxml()),
    ],
)
async def test_valid_score(format: ScoreFormat, content: bytes) -> None:
    assert not (await MusicXmlScoreValidator().validate(format, content)).errors


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("format", "content"),
    [
        (ScoreFormat.PDF, score_samples.pdf()),
        (ScoreFormat.MUSICXML, b"<score-partwise>"),
        (ScoreFormat.COMPRESSED_MUSICXML, b"PK broken"),
        (
            ScoreFormat.COMPRESSED_MUSICXML,
            score_samples.zip_archive({"score.musicxml": b"<html/>"}),
        ),
        (
            ScoreFormat.COMPRESSED_MUSICXML,
            score_samples.zip_archive(
                {
                    "META-INF/container.xml": score_samples.CONTAINER_XML.replace(
                        "score.musicxml", "../score.musicxml"
                    ).encode("utf-8"),
                    "../score.musicxml": score_samples.musicxml(),
                }
            ),
        ),
    ],
)
async def test_invalid_score(format: ScoreFormat, content: bytes) -> None:
    assert (await MusicXmlScoreValidator().validate(format, content)).errors
