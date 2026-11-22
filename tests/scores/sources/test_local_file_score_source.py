# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Integration tests of the score read from a local file."""

from pathlib import Path

import pytest

from my_beautiful_choir.scores.errors import InvalidScoreSizeError
from my_beautiful_choir.scores.score_origin import ScoreOrigin
from my_beautiful_choir.scores.sources.errors import ScoreSourceError, UnreadableLocalFileError
from my_beautiful_choir.scores.sources.local_file_score_source import LocalFileScoreSource
from my_beautiful_choir.scores.sources.score_content import ScoreContent
from tests import score_samples


@pytest.mark.anyio
async def test_reads_the_file_and_its_name(tmp_path: Path) -> None:
    path = tmp_path / "Ave Maria.pdf"
    path.write_bytes(score_samples.pdf())
    source = LocalFileScoreSource(path)
    assert source.origin is ScoreOrigin.LOCAL_FILE
    assert source.link is None
    fetched = await source.fetch(limit=1024)
    assert fetched == ScoreContent(original_name="Ave Maria.pdf", content=score_samples.pdf())


@pytest.mark.anyio
async def test_reads_a_file_of_exactly_the_limit(tmp_path: Path) -> None:
    path = tmp_path / "score.pdf"
    path.write_bytes(b"12345")
    assert (await LocalFileScoreSource(path).fetch(limit=5)).content == b"12345"


@pytest.mark.anyio
async def test_a_file_over_the_limit_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "score.pdf"
    path.write_bytes(b"123456")
    with pytest.raises(InvalidScoreSizeError):
        await LocalFileScoreSource(path).fetch(limit=5)


@pytest.mark.anyio
async def test_the_home_directory_is_expanded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    (tmp_path / "score.pdf").write_bytes(b"content")
    fetched = await LocalFileScoreSource(Path("~") / "score.pdf").fetch(limit=1024)
    assert fetched.content == b"content"


@pytest.mark.anyio
async def test_a_missing_file_is_unreadable(tmp_path: Path) -> None:
    path = tmp_path / "missing.pdf"
    with pytest.raises(UnreadableLocalFileError) as raised:
        await LocalFileScoreSource(path).fetch(limit=1024)
    assert raised.value.path == path
    assert isinstance(raised.value, ScoreSourceError)
    assert str(path) in str(raised.value)


@pytest.mark.anyio
async def test_a_directory_is_unreadable(tmp_path: Path) -> None:
    with pytest.raises(UnreadableLocalFileError):
        await LocalFileScoreSource(tmp_path).fetch(limit=1024)


@pytest.mark.anyio
async def test_a_relative_path_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("score.pdf").write_bytes(b"content")
    with pytest.raises(UnreadableLocalFileError) as raised:
        await LocalFileScoreSource(Path("score.pdf")).fetch(limit=1024)
    assert raised.value.reason == "the path is not absolute"


@pytest.mark.anyio
async def test_an_unknown_home_directory_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(self: Path) -> Path:
        raise RuntimeError("Could not determine home directory.")

    monkeypatch.setattr(Path, "expanduser", fail)
    with pytest.raises(UnreadableLocalFileError) as raised:
        await LocalFileScoreSource(Path("~/score.pdf")).fetch(limit=1024)
    assert raised.value.reason == "the home directory is unknown"


@pytest.mark.anyio
async def test_a_read_failure_is_reported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "score.pdf"
    path.write_bytes(b"content")

    def deny(self: Path, *arguments: object, **keywords: object) -> None:
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(Path, "open", deny)
    with pytest.raises(UnreadableLocalFileError) as raised:
        await LocalFileScoreSource(path).fetch(limit=1024)
    assert raised.value.reason == "Permission denied"
