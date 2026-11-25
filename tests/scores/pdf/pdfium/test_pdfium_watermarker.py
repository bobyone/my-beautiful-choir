# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Validate the vector watermark on multiple page sizes."""

from contextlib import closing
from io import BytesIO

import pypdfium2 as pdfium
import pytest
from PIL import Image

from my_beautiful_choir.scores.pdf.errors import ScorePdfExportError
from my_beautiful_choir.scores.pdf.pdfium.pdfium_watermarker import PdfiumWatermarker


@pytest.mark.anyio
async def test_watermark_every_page() -> None:
    with (
        Image.new("RGB", (400, 600), "white") as first,
        Image.new("RGB", (600, 400), "white") as second,
        BytesIO() as source,
    ):
        first.save(source, format="PDF", save_all=True, append_images=[second])
        pdf = await PdfiumWatermarker().mark_draft(source.getvalue())
    with pdfium.PdfDocument(pdf) as document:
        assert len(document) == 2
        for page in document:
            with closing(page), closing(page.get_textpage()) as text:
                assert "DRAFT" in text.get_text_bounded()


@pytest.mark.anyio
async def test_watermark_refuses_broken_pdf() -> None:
    with pytest.raises(ScorePdfExportError, match="watermark"):
        await PdfiumWatermarker().mark_draft(b"%PDF-broken")
