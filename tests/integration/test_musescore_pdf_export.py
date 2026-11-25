# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Test real local MuseScore Studio if the test executable is configured."""

import os
from contextlib import closing
from pathlib import Path

import pypdfium2 as pdfium
import pytest

from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.pdf.errors import ScorePdfExportError
from my_beautiful_choir.scores.pdf.musescore.musescore_pdf_exporter import MuseScorePdfExporter
from my_beautiful_choir.scores.pdf.pdfium.pdfium_watermarker import PdfiumWatermarker
from tests import score_samples


@pytest.mark.anyio
async def test_export_requires_configured_executable() -> None:
    with pytest.raises(ScorePdfExportError, match="absolute path"):
        await MuseScorePdfExporter(None, 60).export(ScoreFormat.MUSICXML, score_samples.musicxml())


@pytest.mark.anyio
async def test_local_export_and_watermark() -> None:
    executable = os.environ.get("MBC_TEST_MUSESCORE_EXE")
    if executable is None:
        pytest.skip("Set MBC_TEST_MUSESCORE_EXE to exercise the local adapter.")
    musicxml = (
        score_samples.musicxml_text()
        .replace(
            '<measure number="1"/>',
            '<measure number="1"><note><rest measure="yes"/><duration>4</duration></note></measure>'
            '<measure number="2"><print new-page="yes"/>'
            '<note><rest measure="yes"/><duration>4</duration></note></measure>',
        )
        .encode("utf-8")
    )
    exporter = MuseScorePdfExporter(Path(executable), 30)
    exported = await exporter.export(ScoreFormat.MUSICXML, musicxml)
    marked = await PdfiumWatermarker().mark_draft(exported)
    with pdfium.PdfDocument(marked) as document:
        assert len(document) == 2
        for page in document:
            with closing(page), closing(page.get_textpage()) as text:
                assert "DRAFT" in text.get_text_bounded()
