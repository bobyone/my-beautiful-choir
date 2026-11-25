# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Contract for marking rendered draft PDF pages."""

from abc import ABC, abstractmethod


class PdfWatermarker(ABC):
    """Mark every page of a PDF as a draft."""

    @abstractmethod
    async def mark_draft(self, pdf: bytes) -> bytes:
        """Return a marked PDF or fail without returning any pages."""
