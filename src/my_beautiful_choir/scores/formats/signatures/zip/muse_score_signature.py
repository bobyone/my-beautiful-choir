# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Signature of the MuseScore format."""

from collections.abc import Sequence

from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.formats.signatures.zip.zip_archive_signature import (
    ZipArchiveSignature,
)


class MuseScoreSignature(ZipArchiveSignature):
    """A MuseScore file (``.mscz``) is a zip archive holding a ``.mscx`` score."""

    @property
    def format(self) -> ScoreFormat:
        return ScoreFormat.MUSESCORE

    def matches_entries(self, names: Sequence[str]) -> bool:
        return any(name.lower().endswith(".mscx") for name in names)
