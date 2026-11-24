# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Render source pages with PDFium and transfer them to the MCP client as PNG images."""

import asyncio
from io import BytesIO
from threading import Lock

from my_beautiful_choir.scores.pdf.errors import PdfPageError
from my_beautiful_choir.scores.pdf.pdf_page_renderer import PdfPageRenderer

_MAX_DIMENSION = 1800
_PDFIUM_LOCK = Lock()


class PdfiumPageRenderer(PdfPageRenderer):
    """Use the optional personal-mode PDF rendering package."""

    async def render(self, pdf: bytes, page_number: int) -> tuple[bytes, int]:
        """Render one PDF page without reading the remaining pages."""
        return await asyncio.to_thread(_render, pdf, page_number)


def _render(pdf: bytes, page_number: int) -> tuple[bytes, int]:
    try:
        import pypdfium2 as pdfium
    except ImportError as error:
        raise PdfPageError("Install the personal-ocr extra to read source pages.") from error
    try:
        with _PDFIUM_LOCK, pdfium.PdfDocument(pdf) as document:
            count = len(document)
            if not 1 <= page_number <= count:
                raise PdfPageError(f"Choose a page from 1 to {count}.")
            page = document[page_number - 1]
            width, height = page.get_size()
            if min(width, height) <= 0:
                raise PdfPageError("Choose a PDF with readable page dimensions.")
            bitmap = page.render(scale=min(3, _MAX_DIMENSION / max(width, height)))
            with bitmap.to_pil() as image, BytesIO() as output:
                image.save(output, format="PNG")
                return output.getvalue(), count
    except (pdfium.PdfiumError, OSError, ValueError) as error:
        raise PdfPageError("The source page could not be read. Check the PDF.") from error
