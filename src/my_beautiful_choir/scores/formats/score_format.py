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

    @property
    def media_type(self) -> str:
        """Media type of a file of this format.

        MuseScore has no registered media type: the unregistered one used in
        practice is given.
        """
        return _MEDIA_TYPES[self]


_MEDIA_TYPES = {
    ScoreFormat.PDF: "application/pdf",
    ScoreFormat.MUSICXML: "application/vnd.recordare.musicxml+xml",
    ScoreFormat.COMPRESSED_MUSICXML: "application/vnd.recordare.musicxml",
    ScoreFormat.MUSESCORE: "application/x-musescore",
}

_DISPLAY_NAMES = {
    ScoreFormat.PDF: "PDF",
    ScoreFormat.MUSICXML: "MusicXML",
    ScoreFormat.COMPRESSED_MUSICXML: "compressed MusicXML",
    ScoreFormat.MUSESCORE: "MuseScore",
}
