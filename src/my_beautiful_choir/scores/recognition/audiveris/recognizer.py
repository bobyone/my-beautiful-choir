# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Audiveris adapter for full PDF transcription in batch mode."""

import asyncio
import subprocess
import sys
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
from my_beautiful_choir.scores.score_rules import MAXIMUM_SIZE


class AudiverisRecognizer(ScoreRecognizer):
    """Run Audiveris in a disposable directory and return its single uncompressed export."""

    def __init__(self, installation: AudiverisInstallation, timeout_seconds: int) -> None:
        self._installation = installation
        self._timeout = timeout_seconds

    async def transcribe(self, pdf: bytes) -> bytes:
        """Transcribe a PDF with a locally installed Audiveris."""
        command = await self._installation.command()
        with TemporaryDirectory(prefix="mbc-transcription-") as directory:
            workspace = Path(directory)
            source = workspace / "source.pdf"
            source.write_bytes(pdf)
            output = workspace / "output"
            output.mkdir()
            if len(command) == 3 and command[1] == "run":
                command = (*command[:2], f"--filesystem={workspace}", command[2])
            await self._run(
                *command,
                "-batch",
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
            exports = sorted(
                path
                for path in output.rglob("*")
                if path.suffix.casefold() in {".xml", ".musicxml"}
                and path.is_file()
                and not path.is_symlink()
                and path.resolve().is_relative_to(output.resolve())
            )
            if not exports:
                raise RecognitionError("Audiveris did not produce a MusicXML score. Check the PDF.")
            if len(exports) != 1:
                raise RecognitionError(
                    "The PDF produced several scores. Transcribe one movement at a time."
                )
            _verify_book(exports[0].with_name("source.omr"))
            with exports[0].open("rb") as stream:
                content = stream.read(MAXIMUM_SIZE + 1)
            if not content or len(content) > MAXIMUM_SIZE:
                raise RecognitionError("The MusicXML transcription is empty or too large.")
            return content

    async def _run(self, *command: str, workspace: Path) -> None:
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=workspace,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
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


def _verify_book(project: Path) -> None:
    """An Audiveris export can omit invalid sheets even when it exits successfully."""
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
