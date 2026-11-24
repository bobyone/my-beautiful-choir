# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Audiveris adapter for full PDF transcription in batch mode."""

import asyncio
import re
import subprocess
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from my_beautiful_choir.scores.recognition.audiveris.installation import AudiverisInstallation
from my_beautiful_choir.scores.recognition.errors import (
    EngineUnavailableError,
    RecognitionError,
)
from my_beautiful_choir.scores.recognition.score_recognizer import ScoreRecognizer
from my_beautiful_choir.scores.sources.local_file_score_source import LocalFileScoreSource
from my_beautiful_choir.scores.sources.score_source import ScoreSource

_EXPORT_NAME = re.compile(r"source(?:\.mvt([1-9][0-9]*))?\.(?:xml|musicxml)", re.IGNORECASE)


class AudiverisRecognizer(ScoreRecognizer):
    """Run Audiveris in a disposable directory and provide its ordered exports."""

    def __init__(
        self, installation: AudiverisInstallation, timeout_seconds: int, cache_directory: Path
    ) -> None:
        self._installation = installation
        self._timeout = timeout_seconds
        self._cache_directory = cache_directory

    @asynccontextmanager
    async def transcribe(self, pdf: bytes) -> AsyncIterator[tuple[ScoreSource, ...]]:
        """Transcribe a PDF and keep the exports available until the caller is done."""
        launch = await self._installation.discover()
        workspace_parent = None
        if launch.flatpak_app_id is not None:
            workspace_parent = self._cache_directory
            workspace_parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix="mbc-transcription-", dir=workspace_parent) as directory:
            workspace = Path(directory)
            source = workspace / "source.pdf"
            source.write_bytes(pdf)
            output = workspace / "output"
            output.mkdir()
            await self._run(
                *launch.command(workspace),
                "-batch",
                "-save",
                "-constant",
                "org.audiveris.omr.sheet.BookManager.useCompression=false",
                "-constant",
                "org.audiveris.omr.sheet.BookManager.useOpus=false",
                "-export",
                "-output",
                str(output),
                "--",
                str(source),
                workspace=workspace,
            )
            yield _movement_sources(output)

    async def _run(self, *command: str, workspace: Path) -> None:
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=workspace,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except OSError as error:
            raise EngineUnavailableError() from error
        try:
            code = await asyncio.wait_for(process.wait(), timeout=self._timeout)
        except (TimeoutError, asyncio.CancelledError) as error:
            if process.returncode is None:
                process.kill()
                await process.wait()
            if isinstance(error, asyncio.CancelledError):
                raise
            raise RecognitionError("Transcription timed out. Try a shorter PDF.") from error
        if code != 0:
            raise RecognitionError(
                "Audiveris could not transcribe the complete PDF. Check the source."
            )


def _movement_sources(output: Path) -> tuple[ScoreSource, ...]:
    """Match all movement exports to the verified Audiveris project."""
    root = output.resolve()
    projects = [
        path
        for path in output.rglob("source.omr")
        if path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root)
    ]
    if len(projects) != 1:
        raise RecognitionError("Audiveris could not confirm that it processed the full PDF.")
    project = projects[0]
    count = _movement_count(project)
    exports: dict[int, Path] = {}
    for path in project.parent.iterdir():
        match = _EXPORT_NAME.fullmatch(path.name)
        if match is None:
            continue
        number = match[1]
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise RecognitionError("Audiveris did not produce a complete set of movement exports.")
        if (number is None) != (count == 1):
            raise RecognitionError("Audiveris did not produce a complete set of movement exports.")
        # File names are bounded by the filesystem. Compare against the project before publishing.
        position = int(number) if number else 1
        if position in exports:
            raise RecognitionError("Audiveris produced duplicate movement exports.")
        exports[position] = path
    if exports.keys() != set(range(1, count + 1)):
        raise RecognitionError("Audiveris did not produce a complete set of movement exports.")
    return tuple(LocalFileScoreSource(exports[number]) for number in range(1, count + 1))


def _movement_count(project: Path) -> int:
    """Return the movement count only if all source sheets have been processed."""
    try:
        if project.is_symlink():
            raise ValueError("Unexpected project symlink.")
        with ZipFile(project) as archive, archive.open("book.xml") as stream:
            metadata = stream.read(2 * 1024 * 1024 + 1).decode("utf-8")
        if len(metadata) > 2 * 1024 * 1024 or "<!DOCTYPE" in metadata.upper():
            raise ValueError("Unexpected Audiveris project metadata.")
        book = ElementTree.fromstring(metadata)  # noqa: S314
    except (BadZipFile, ElementTree.ParseError, KeyError, OSError, ValueError) as error:
        raise RecognitionError(
            "Audiveris could not confirm that it processed the full PDF."
        ) from error
    sheets = book.findall("sheet")
    if not sheets or any(
        sheet.get("invalid", "").lower() in {"true", "1"}
        or "PAGE" not in (sheet.findtext("steps") or "").split()
        or sheet.find("page") is None
        for sheet in sheets
    ):
        raise RecognitionError(
            "Audiveris skipped a page. Check every page of the PDF and try again."
        )
    count = len(book.findall("score"))
    if not count:
        raise RecognitionError("Audiveris did not detect any movement. Check the source PDF.")
    return count
