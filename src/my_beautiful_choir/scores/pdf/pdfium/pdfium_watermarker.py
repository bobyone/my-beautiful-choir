# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Add a vector DRAFT watermark to every page using PDFium."""

import asyncio
from contextlib import closing
from ctypes import c_ushort
from io import BytesIO

from my_beautiful_choir.scores.pdf.errors import ScorePdfExportError
from my_beautiful_choir.scores.pdf.pdf_watermarker import PdfWatermarker
from my_beautiful_choir.scores.pdf.pdfium.pdfium_lock import PDFIUM_LOCK
from my_beautiful_choir.scores.score_rules import MAXIMUM_SIZE


class PdfiumWatermarker(PdfWatermarker):
    """Mark every exported draft page using the optional PDFium installation."""

    async def mark_draft(self, pdf: bytes) -> bytes:
        return await asyncio.to_thread(_mark_draft, pdf)


def _mark_draft(pdf: bytes) -> bytes:
    try:
        import pypdfium2 as pdfium
        from pypdfium2 import raw
    except ImportError as error:
        raise ScorePdfExportError(
            "Install the personal-ocr extra to mark draft PDF pages."
        ) from error
    try:
        with PDFIUM_LOCK, pdfium.PdfDocument(pdf) as document, BytesIO() as output:
            if len(document) == 0:
                raise ScorePdfExportError("The exported PDF has no pages.")
            watermark = (c_ushort * 6)(*map(ord, "DRAFT"), 0)
            for page in document:
                with closing(page):
                    width, height = page.get_size()
                    if min(width, height) <= 0:
                        raise ScorePdfExportError("The exported PDF has invalid page dimensions.")
                    text = raw.FPDFPageObj_NewTextObj(
                        document.raw, b"Helvetica-Bold", min(width, height) / 5
                    )
                    if not text:
                        raise ScorePdfExportError("Could not create the draft watermark.")
                    if not (
                        raw.FPDFText_SetText(text, watermark)
                        and raw.FPDFPageObj_SetFillColor(text, 98, 98, 98, 96)
                    ):
                        raw.FPDFPageObj_Destroy(text)
                        raise ScorePdfExportError("Could not prepare the draft watermark.")
                    raw.FPDFPageObj_Transform(
                        text, 0.94, 0.34, -0.34, 0.94, width * 0.19, height * 0.38
                    )
                    raw.FPDFPage_InsertObject(page.raw, text)
                    page.gen_content()
            document.save(output)
            if output.tell() > MAXIMUM_SIZE:
                raise ScorePdfExportError("The watermarked PDF exceeds the download size limit.")
            return output.getvalue()
    except (pdfium.PdfiumError, OSError, ValueError) as error:
        raise ScorePdfExportError("Could not watermark all draft PDF pages.") from error
