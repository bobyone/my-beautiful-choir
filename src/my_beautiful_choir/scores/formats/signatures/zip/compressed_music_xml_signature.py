# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Signature of the compressed MusicXML format."""

from collections.abc import Sequence

from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.formats.signatures.zip.zip_archive_signature import (
    ZipArchiveSignature,
)

CONTAINER = "META-INF/container.xml"


class CompressedMusicXmlSignature(ZipArchiveSignature):
    """A compressed MusicXML file (``.mxl``) is a zip archive holding ``META-INF/container.xml``
    and a ``.musicxml`` or ``.xml`` score, but no MuseScore score (``.mscx``).

    MuseScore files also hold ``META-INF/container.xml``: the absence of a
    ``.mscx`` entry tells them apart.
    """

    @property
    def format(self) -> ScoreFormat:
        return ScoreFormat.COMPRESSED_MUSICXML

    def matches_entries(self, names: Sequence[str]) -> bool:
        lowered = [name.lower() for name in names]
        return (
            CONTAINER in names
            and not any(name.endswith(".mscx") for name in lowered)
            and any(
                name.endswith((".musicxml", ".xml")) and not name.startswith("meta-inf/")
                for name in lowered
            )
        )
