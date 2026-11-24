# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Audiveris batch output handling on an isolated filesystem."""

from pathlib import Path

import pytest

from my_beautiful_choir.scores.recognition.audiveris.installation import AudiverisInstallation
from my_beautiful_choir.scores.recognition.audiveris.launch import AudiverisLaunch
from my_beautiful_choir.scores.recognition.audiveris.recognizer import AudiverisRecognizer
from my_beautiful_choir.scores.recognition.errors import RecognitionError
from my_beautiful_choir.scores.score_rules import MAXIMUM_SIZE
from tests import score_samples


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("invalid", "movements", "save_project", "flatpak", "missing", "duplicate", "message"),
    [
        (False, 1, True, False, False, False, None),
        (False, 11, True, True, False, False, None),
        (True, 1, True, False, False, False, "skipped a page"),
        (False, 2, True, False, True, False, "complete set"),
        (False, 2, True, False, False, True, "duplicate movement"),
        (False, 1, False, False, False, False, "could not confirm"),
    ],
)
async def test_batch_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    invalid: bool,
    movements: int,
    save_project: bool,
    flatpak: bool,
    missing: bool,
    duplicate: bool,
    message: str | None,
) -> None:
    installation = AudiverisInstallation(None, "unknown", {}, tmp_path)
    cache = tmp_path / "cache"
    recognizer = AudiverisRecognizer(installation, 5, cache)

    async def discover() -> AudiverisLaunch:
        if flatpak:
            return AudiverisLaunch(Path("flatpak"), flatpak_app_id="org.audiveris.audiveris")
        return AudiverisLaunch(Path("Audiveris"))

    monkeypatch.setattr(installation, "discover", discover)
    used_workspace: Path | None = None

    async def run(*args: str, workspace: Path) -> None:
        nonlocal used_workspace
        output = Path(args[args.index("-output") + 1])
        assert output.parent == workspace
        assert "-save" in args
        if flatpak:
            assert workspace.parent == cache
            assert args[:4] == (
                "flatpak",
                "run",
                f"--filesystem={workspace}",
                "org.audiveris.audiveris",
            )
        else:
            assert args[0] == "Audiveris"
            assert workspace.parent != cache
        used_workspace = workspace
        assert Path(args[-1]).read_bytes() == score_samples.pdf()
        for number in reversed(range(1, movements + 1 - int(missing))):
            name = f"source.mvt{number}.xml" if movements > 1 else "source.xml"
            content = score_samples.musicxml().replace(b"Soprano", f"Movement {number}".encode())
            (output / name).write_bytes(content)
            if duplicate and number == 1:
                (output / "source.mvt1.musicxml").write_bytes(content)
        invalid_attribute = ' invalid="true"' if invalid else ""
        sheet_stats = b"<steps>LOAD PAGE</steps><page/>"
        metadata = (
            b"<book><sheet>"
            + sheet_stats
            + b"</sheet>"
            + f"<sheet{invalid_attribute}>".encode()
            + sheet_stats
            + b"</sheet>"
            + b"<score/>" * movements
            + b"</book>"
        )
        if save_project:
            (output / "source.omr").write_bytes(score_samples.zip_archive({"book.xml": metadata}))

    monkeypatch.setattr(recognizer, "_run", run)
    if message is None:
        async with recognizer.transcribe(score_samples.pdf()) as exports:
            contents = [await source.fetch(MAXIMUM_SIZE) for source in exports]
            expected = [
                score_samples.musicxml().replace(b"Soprano", f"Movement {number}".encode())
                for number in range(1, movements + 1)
            ]
            assert [content.content for content in contents] == expected
    else:
        with pytest.raises(RecognitionError, match=message):
            async with recognizer.transcribe(score_samples.pdf()):
                pytest.fail("Unexpected successful transcription.")
    assert used_workspace is not None
    assert not used_workspace.exists()
