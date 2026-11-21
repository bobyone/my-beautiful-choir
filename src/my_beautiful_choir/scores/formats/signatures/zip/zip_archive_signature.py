# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Signature of the score formats stored as zip archives."""

import io
import zipfile
from abc import abstractmethod
from collections.abc import Sequence

from my_beautiful_choir.scores.formats.score_format_signature import ScoreFormatSignature

LOCAL_FILE_HEADER = b"PK\x03\x04"


class ZipArchiveSignature(ScoreFormatSignature):
    """Recognizes a zip archive from the names of its entries.

    Only the index of the archive is read: no entry is decompressed, so an
    archive crafted to expand enormously does no harm.
    """

    def matches(self, content: bytes) -> bool:
        if not content.startswith(LOCAL_FILE_HEADER):
            return False
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                names = archive.namelist()
        except (zipfile.BadZipFile, zipfile.LargeZipFile, ValueError, OSError, EOFError):
            return False
        return self.matches_entries(names)

    @abstractmethod
    def matches_entries(self, names: Sequence[str]) -> bool:
        """Whether an archive holding entries with these names is of this format."""
