# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Audiveris batch output handling on an isolated filesystem."""

from pathlib import Path

import pytest

from my_beautiful_choir.scores.recognition.audiveris.installation import AudiverisInstallation
from my_beautiful_choir.scores.recognition.audiveris.recognizer import AudiverisRecognizer
from my_beautiful_choir.scores.recognition.errors import RecognitionError
from tests import score_samples


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("invalid", "movements", "message"),
    [(False, 1, None), (True, 1, "skipped a page"), (False, 2, "several scores")],
)
async def test_batch_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    invalid: bool,
    movements: int,
    message: str | None,
) -> None:
    installation = AudiverisInstallation(None, "unknown", {}, tmp_path)
    recognizer = AudiverisRecognizer(installation, 5)
    monkeypatch.setattr(installation, "command", _command)
    used_workspace: Path | None = None

    async def run(*args: str, workspace: Path) -> None:
        nonlocal used_workspace
        output = Path(args[args.index("-output") + 1])
        assert output.parent == workspace
        used_workspace = workspace
        assert Path(args[-1]).read_bytes() == score_samples.pdf()
        for number in range(movements):
            (output / f"source-{number}.xml").write_bytes(score_samples.musicxml())
        invalid_attribute = ' invalid="true"' if invalid else ""
        sheet_stats = b"<steps>LOAD PAGE</steps><page/>"
        metadata = (
            b"<book><sheet>"
            + sheet_stats
            + b"</sheet>"
            + f"<sheet{invalid_attribute}>".encode()
            + sheet_stats
            + b"</sheet></book>"
        )
        (output / "source.omr").write_bytes(score_samples.zip_archive({"book.xml": metadata}))

    monkeypatch.setattr(recognizer, "_run", run)
    if message is None:
        assert await recognizer.transcribe(score_samples.pdf()) == score_samples.musicxml()
    else:
        with pytest.raises(RecognitionError, match=message):
            await recognizer.transcribe(score_samples.pdf())
    assert used_workspace is not None
    assert not used_workspace.exists()


async def _command() -> tuple[str, ...]:
    return ("Audiveris",)
