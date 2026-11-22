# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Supported score formats."""

from enum import StrEnum


class ScoreFormat(StrEnum):
    """Type of file of a score; the value is its usual file extension, without the dot."""

    PDF = "pdf"
    MUSICXML = "musicxml"
    COMPRESSED_MUSICXML = "mxl"
    MUSESCORE = "mscz"

    @property
    def display_name(self) -> str:
        """English name of the format, as said to the model."""
        return _DISPLAY_NAMES[self]

    @property
    def extension(self) -> str:
        """Usual file extension, with its dot."""
        return f".{self.value}"


_DISPLAY_NAMES = {
    ScoreFormat.PDF: "PDF",
    ScoreFormat.MUSICXML: "MusicXML",
    ScoreFormat.COMPRESSED_MUSICXML: "compressed MusicXML",
    ScoreFormat.MUSESCORE: "MuseScore",
}
