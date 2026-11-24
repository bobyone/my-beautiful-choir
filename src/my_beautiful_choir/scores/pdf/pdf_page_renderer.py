# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Render a source score page for verification."""

from abc import ABC, abstractmethod


class PdfPageRenderer(ABC):
    """Return an image and the total page count for a one-based PDF page."""

    @abstractmethod
    async def render(self, pdf: bytes, page_number: int) -> tuple[bytes, int]:
        """Return PNG data or raise PdfPageError."""
