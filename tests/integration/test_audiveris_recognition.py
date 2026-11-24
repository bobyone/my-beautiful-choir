# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Opt-in check of the real Audiveris batch project and MusicXML export."""

import os
import sys
from pathlib import Path

import pytest
from platformdirs import user_cache_path

from my_beautiful_choir.scores.musicxml.musicxml_document import musicxml_text
from my_beautiful_choir.scores.pdf.pdfium.pdfium_page_renderer import PdfiumPageRenderer
from my_beautiful_choir.scores.recognition.audiveris.installation import AudiverisInstallation
from my_beautiful_choir.scores.recognition.audiveris.recognizer import AudiverisRecognizer
from my_beautiful_choir.scores.recognition.errors import EngineNotFoundError


@pytest.mark.anyio
async def test_real_audiveris_transcribes_full_pdf() -> None:
    sample = os.environ.get("MBC_TEST_AUDIVERIS_PDF")
    if not sample:
        pytest.skip("Set MBC_TEST_AUDIVERIS_PDF to a continuous, multipage score.")
    override = os.environ.get("MBC_TEST_AUDIVERIS_EXECUTABLE")
    installation = AudiverisInstallation(
        Path(override) if override else None, sys.platform, os.environ, Path.home()
    )
    try:
        await installation.discover()
    except EngineNotFoundError:
        pytest.skip("Audiveris is not installed.")
    pdf = Path(sample).read_bytes()
    _, page_count = await PdfiumPageRenderer().render(pdf, 1)
    assert page_count >= 2
    # The adapter checks the real .omr archive before returning the MusicXML.
    cache = user_cache_path("my-beautiful-choir-tests")
    output = await AudiverisRecognizer(installation, 180, cache).transcribe(pdf)
    assert "<note" in musicxml_text(output)
