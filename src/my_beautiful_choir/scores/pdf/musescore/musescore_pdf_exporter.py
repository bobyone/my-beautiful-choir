# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Local MuseScore Studio adapter for exporting a score copy."""

import asyncio
from contextlib import suppress
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree

from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.musicxml.compressed_musicxml_document import (
    compressed_musicxml_bytes,
)
from my_beautiful_choir.scores.musicxml.errors import InvalidMusicXmlError
from my_beautiful_choir.scores.musicxml.musicxml_document import musicxml_text
from my_beautiful_choir.scores.pdf.errors import ScorePdfExportError
from my_beautiful_choir.scores.pdf.score_pdf_exporter import ScorePdfExporter
from my_beautiful_choir.scores.score_rules import MAXIMUM_SIZE


class MuseScorePdfExporter(ScorePdfExporter):
    """Run a configured executable with fixed arguments and disposable files."""

    def __init__(self, executable: Path | None, timeout_seconds: int) -> None:
        self._executable = executable
        self._timeout_seconds = timeout_seconds
        self._job = asyncio.Lock()

    async def export(self, score_format: ScoreFormat, content: bytes) -> bytes:
        executable = self._executable
        if executable is None or not executable.is_absolute() or not executable.is_file():
            raise ScorePdfExportError(
                "Configure the absolute path to the MuseScore Studio executable."
            )
        try:
            content = await asyncio.to_thread(_export_document, score_format, content)
        except InvalidMusicXmlError as error:
            raise ScorePdfExportError(str(error)) from error
        async with self._job:
            return await self._export(executable, content)

    async def _export(self, executable: Path, content: bytes) -> bytes:
        try:
            with TemporaryDirectory(prefix="mbc-score-pdf-") as directory:
                workspace = Path(directory)
                source = workspace / "score.musicxml"
                output = workspace / "score.pdf"
                await asyncio.to_thread(source.write_bytes, content)
                process = await asyncio.create_subprocess_exec(
                    str(executable),
                    "-R",
                    "-o",
                    str(output),
                    str(source),
                    cwd=workspace,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                try:
                    exit_code = await asyncio.wait_for(process.wait(), self._timeout_seconds)
                except (TimeoutError, asyncio.CancelledError):
                    if process.returncode is None:
                        with suppress(ProcessLookupError):
                            process.kill()
                    await process.wait()
                    raise
                if exit_code:
                    raise ScorePdfExportError("MuseScore Studio could not render this score.")
                return await asyncio.to_thread(_read_pdf, output)
        except TimeoutError as error:
            raise ScorePdfExportError(
                "The PDF export took too long. Try a smaller score."
            ) from error
        except OSError as error:
            raise ScorePdfExportError("Could not run MuseScore Studio or read its PDF.") from error


def _export_document(score_format: ScoreFormat, content: bytes) -> bytes:
    if score_format is ScoreFormat.COMPRESSED_MUSICXML:
        content = compressed_musicxml_bytes(content)
    elif score_format is not ScoreFormat.MUSICXML:
        raise ScorePdfExportError("Choose a MusicXML score to export.")
    musicxml_text(content)
    # Validation above rejects entity declarations. Reserialising leaves out the DTD.
    document = ElementTree.fromstring(content)  # noqa: S314
    for element in document.iter():
        if element.tag.rsplit("}", 1)[-1] in {"image", "credit-image"} and element.get("source"):
            raise ScorePdfExportError("Export a score without linked images to render it locally.")
    with BytesIO() as result:
        ElementTree.ElementTree(document).write(result, encoding="utf-8", xml_declaration=True)
        return result.getvalue()


def _read_pdf(path: Path) -> bytes:
    with path.open("rb") as file:
        content = file.read(MAXIMUM_SIZE + 1)
    if not content.startswith(b"%PDF-") or len(content) > MAXIMUM_SIZE:
        raise ScorePdfExportError("MuseScore Studio returned an invalid or oversized PDF.")
    return content
