# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Integration tests of the system score opener, with a double of the system command."""

import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from my_beautiful_choir.scores.errors import ScoreOpenError
from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.opening.system.system_score_opener import (
    SystemScoreOpener,
    system_launcher,
)
from my_beautiful_choir.scores.score import Score
from my_beautiful_choir.scores.score_origin import ScoreOrigin


def _score(label: str = "Alto part", score_format: ScoreFormat = ScoreFormat.MUSESCORE) -> Score:
    score_id = uuid4()
    return Score(
        id=score_id,
        work_id=uuid4(),
        label=label,
        format=score_format,
        size=7,
        original_name="original.mscz",
        origin=ScoreOrigin.LOCAL_FILE,
        link=None,
        storage_key=f"choirs/c/scores/{score_id}",
        added_at=datetime(2026, 11, 21, tzinfo=UTC),
    )


class _SpyLauncher:
    def __init__(self, error: Exception | None = None) -> None:
        self.paths: list[Path] = []
        self.error = error

    def __call__(self, path: Path) -> None:
        self.paths.append(path)
        if self.error is not None:
            raise self.error


@pytest.mark.anyio
async def test_opens_a_temporary_copy_named_after_the_label(tmp_path: Path) -> None:
    launcher = _SpyLauncher()
    score = _score()
    await SystemScoreOpener(tmp_path, launcher).open(score, b"content")
    [path] = launcher.paths
    assert path == tmp_path / str(score.id) / "Alto part.mscz"
    assert path.read_bytes() == b"content"


@pytest.mark.anyio
async def test_opening_again_replaces_the_copy(tmp_path: Path) -> None:
    launcher = _SpyLauncher()
    opener = SystemScoreOpener(tmp_path, launcher)
    score = _score()
    await opener.open(score, b"first")
    await opener.open(score, b"second")
    assert launcher.paths[0] == launcher.paths[1]
    assert launcher.paths[1].read_bytes() == b"second"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("label", "file_name"),
    [
        ("../../secret", "_secret.pdf"),
        ("C:\\Windows\\x", "C_Windows_x.pdf"),
        ("Ave Maria: Soprano/Alto", "Ave Maria_ Soprano_Alto.pdf"),
        ("Chœur", "Chœur.pdf"),
        ("...", "_.pdf"),
        ("", "score.pdf"),
        ("a" * 150, "a" * 100 + ".pdf"),
    ],
)
async def test_the_label_cannot_leave_the_directory(
    tmp_path: Path, label: str, file_name: str
) -> None:
    launcher = _SpyLauncher()
    score = _score(label, ScoreFormat.PDF)
    await SystemScoreOpener(tmp_path, launcher).open(score, b"content")
    assert launcher.paths == [tmp_path / str(score.id) / file_name]


@pytest.mark.anyio
async def test_no_application_for_the_format(tmp_path: Path) -> None:
    opener = SystemScoreOpener(tmp_path, _SpyLauncher(OSError(1155, "No application")))
    with pytest.raises(ScoreOpenError) as raised:
        await opener.open(_score(), b"content")
    assert raised.value.format is ScoreFormat.MUSESCORE
    assert "MuseScore files (.mscz)" in str(raised.value)


@pytest.mark.anyio
async def test_unwritable_temporary_directory(tmp_path: Path) -> None:
    directory = tmp_path / "file"
    directory.write_text("not a directory", encoding="utf-8")
    launcher = _SpyLauncher()
    with pytest.raises(ScoreOpenError) as raised:
        await SystemScoreOpener(directory, launcher).open(_score(), b"content")
    assert "temporary copy" in raised.value.reason
    assert launcher.paths == []


def test_personal_mode_uses_the_temporary_directory_of_the_system() -> None:
    opener = SystemScoreOpener.in_temporary_directory()
    assert opener.directory == Path(tempfile.gettempdir()) / "my-beautiful-choir"


@pytest.mark.parametrize(("platform", "command"), [("darwin", "open"), ("linux", "xdg-open")])
def test_system_launcher_runs_the_command_of_the_platform(
    monkeypatch: pytest.MonkeyPatch, platform: str, command: str
) -> None:
    calls: list[tuple[list[str], dict[str, object]]] = []

    def run(arguments: list[str], **options: object) -> None:
        calls.append((arguments, options))

    monkeypatch.setattr(subprocess, "run", run)
    system_launcher(platform)(Path("score.pdf"))
    [(arguments, options)] = calls
    assert arguments == [command, "score.pdf"]
    assert options["check"] is True
    assert options["stdin"] is subprocess.DEVNULL


def test_system_launcher_of_windows_starts_the_file(monkeypatch: pytest.MonkeyPatch) -> None:
    started: list[Path] = []
    monkeypatch.setattr(os, "startfile", started.append, raising=False)
    system_launcher("win32")(Path("score.pdf"))
    assert started == [Path("score.pdf")]


@pytest.mark.anyio
async def test_a_failing_command_cannot_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def run(arguments: list[str], **options: object) -> None:
        raise subprocess.CalledProcessError(3, arguments)

    monkeypatch.setattr(subprocess, "run", run)
    opener = SystemScoreOpener(tmp_path, system_launcher("linux"))
    with pytest.raises(ScoreOpenError):
        await opener.open(_score(), b"content")
