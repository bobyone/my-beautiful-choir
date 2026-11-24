# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Render and validate access to source pages with the personal-mode extras."""

from io import BytesIO

import pytest
from PIL import Image

from my_beautiful_choir.scores.pdf.errors import PdfPageError
from my_beautiful_choir.scores.pdf.pdfium.pdfium_page_renderer import PdfiumPageRenderer


@pytest.mark.anyio
async def test_renders_requested_page_and_reports_total() -> None:
    with (
        Image.new("RGB", (40, 60), "white") as first,
        Image.new("RGB", (60, 40), "black") as second,
        BytesIO() as pdf,
    ):
        first.save(pdf, format="PDF", save_all=True, append_images=[second])
        renderer = PdfiumPageRenderer()
        png, count = await renderer.render(pdf.getvalue(), 2)
        assert count == 2
        with Image.open(BytesIO(png)) as page:
            assert page.width > page.height
            assert page.getpixel((0, 0)) == (0, 0, 0)
        with pytest.raises(PdfPageError, match="1 to 2"):
            await renderer.render(pdf.getvalue(), 3)


@pytest.mark.anyio
async def test_rejects_invalid_pdf() -> None:
    with pytest.raises(PdfPageError, match="Check the PDF"):
        await PdfiumPageRenderer().render(b"%PDF-broken", 1)
