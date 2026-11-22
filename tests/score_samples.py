# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Small sample files of each score format, generated rather than committed."""

import io
import zipfile

MUSICXML_DOCTYPE = (
    '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
    '"http://www.musicxml.org/dtds/partwise.dtd">'
)

CONTAINER_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    "<container><rootfiles>"
    '<rootfile full-path="score.musicxml" media-type="application/vnd.recordare.musicxml+xml"/>'
    "</rootfiles></container>\n"
)


def pdf() -> bytes:
    """A minimal PDF document with one empty page."""
    return (
        b"%PDF-1.7\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] >> endobj\n"
        b"trailer << /Root 1 0 R >>\n%%EOF\n"
    )


def musicxml_text(root: str = "score-partwise") -> str:
    """Text of a minimal MusicXML score, with its declaration and document type."""
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        f"{MUSICXML_DOCTYPE}\n"
        f'<{root} version="4.0">\n'
        '  <part-list><score-part id="P1"><part-name>Soprano</part-name></score-part></part-list>\n'
        '  <part id="P1"><measure number="1"/></part>\n'
        f"</{root}>\n"
    )


def musicxml() -> bytes:
    """A minimal MusicXML score, in UTF-8."""
    return musicxml_text().encode("utf-8")


def zip_archive(entries: dict[str, bytes]) -> bytes:
    """A zip archive holding ``entries``, compressed."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def compressed_musicxml() -> bytes:
    """A minimal compressed MusicXML score (``.mxl``)."""
    return zip_archive(
        {
            "mimetype": b"application/vnd.recordare.musicxml",
            "META-INF/container.xml": CONTAINER_XML.encode("utf-8"),
            "score.musicxml": musicxml(),
        }
    )


def musescore() -> bytes:
    """A minimal MuseScore 4 score (``.mscz``), which also holds a container."""
    return zip_archive(
        {
            "META-INF/container.xml": CONTAINER_XML.replace("score.musicxml", "score.mscx").encode(
                "utf-8"
            ),
            "score.mscx": b'<?xml version="1.0" encoding="UTF-8"?>\n<museScore version="4.20"/>\n',
            "score_style.mss": b"<museScore/>",
            "Thumbnails/thumbnail.png": b"\x89PNG\r\n\x1a\n",
        }
    )
