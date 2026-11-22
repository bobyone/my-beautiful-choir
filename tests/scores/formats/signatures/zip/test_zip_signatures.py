# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the signatures of the formats stored as zip archives."""

import zipfile

import pytest

from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.formats.signatures.zip.compressed_music_xml_signature import (
    CompressedMusicXmlSignature,
)
from my_beautiful_choir.scores.formats.signatures.zip.muse_score_signature import (
    MuseScoreSignature,
)
from tests import score_samples

CONTAINER = {"META-INF/container.xml": score_samples.CONTAINER_XML.encode("utf-8")}

NOT_ZIP_SCORES = [
    b"",
    b"PK\x03\x04",
    b"PK\x03\x04 truncated archive",
    score_samples.compressed_musicxml()[:200],
    score_samples.pdf(),
    score_samples.musicxml(),
    score_samples.zip_archive({"[Content_Types].xml": b"<Types/>", "word/document.xml": b"<w/>"}),
]


def test_recognizes_compressed_musicxml() -> None:
    signature = CompressedMusicXmlSignature()
    assert signature.format is ScoreFormat.COMPRESSED_MUSICXML
    assert signature.matches(score_samples.compressed_musicxml())
    assert signature.matches(
        score_samples.zip_archive({**CONTAINER, "scores/Ave Maria.XML": b"<score-partwise/>"})
    )


@pytest.mark.parametrize(
    "content",
    [
        *NOT_ZIP_SCORES,
        score_samples.musescore(),
        score_samples.zip_archive(CONTAINER),
        score_samples.zip_archive({"score.musicxml": score_samples.musicxml()}),
    ],
)
def test_compressed_musicxml_refuses_other_content(content: bytes) -> None:
    assert not CompressedMusicXmlSignature().matches(content)


def test_recognizes_musescore() -> None:
    signature = MuseScoreSignature()
    assert signature.format is ScoreFormat.MUSESCORE
    assert signature.matches(score_samples.musescore())
    assert signature.matches(score_samples.zip_archive({"Old Score.MSCX": b"<museScore/>"}))


@pytest.mark.parametrize("content", [*NOT_ZIP_SCORES, score_samples.compressed_musicxml()])
def test_musescore_refuses_other_content(content: bytes) -> None:
    assert not MuseScoreSignature().matches(content)


def test_entries_are_never_decompressed(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*arguments: object, **keywords: object) -> None:
        raise AssertionError("an entry was decompressed")

    musescore = score_samples.musescore()
    compressed_musicxml = score_samples.compressed_musicxml()
    monkeypatch.setattr(zipfile.ZipFile, "read", refuse)
    monkeypatch.setattr(zipfile.ZipFile, "open", refuse)
    assert MuseScoreSignature().matches(musescore)
    assert CompressedMusicXmlSignature().matches(compressed_musicxml)
