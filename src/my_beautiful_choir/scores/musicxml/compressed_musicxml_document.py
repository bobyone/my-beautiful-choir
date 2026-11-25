# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Read the main document named in a compressed MusicXML container."""

from io import BytesIO
from pathlib import PurePosixPath
from xml.parsers import expat
from zipfile import BadZipFile, ZipFile

from my_beautiful_choir.scores.formats.signatures.zip.compressed_music_xml_signature import (
    CONTAINER,
)
from my_beautiful_choir.scores.musicxml.errors import InvalidMusicXmlError
from my_beautiful_choir.scores.musicxml.musicxml_document import xml_parser
from my_beautiful_choir.scores.score_rules import MAXIMUM_SIZE

_MANIFEST_LIMIT = 64 * 1024


def _rootfile(manifest: bytes) -> str:
    stack: list[str] = []
    paths: list[str] = []

    def start(name: str, attributes: dict[str, str]) -> None:
        stack.append(name)
        if stack == ["container", "rootfiles", "rootfile"]:
            paths.append(attributes.get("full-path", ""))

    parser = xml_parser()
    parser.StartElementHandler = start
    parser.EndElementHandler = lambda _: stack.pop()
    parser.Parse(manifest, True)
    path = paths[0] if paths else ""
    entry = PurePosixPath(path)
    if (
        not path
        or entry.is_absolute()
        or ".." in entry.parts
        or "\\" in path
        or entry.as_posix() != path
        or path == CONTAINER
    ):
        raise InvalidMusicXmlError("Save the compressed MusicXML with a valid score entry.")
    return path


def _read_entry(archive: ZipFile, name: str, limit: int) -> bytes:
    entries = [entry for entry in archive.infolist() if entry.filename == name]
    if len(entries) != 1 or entries[0].is_dir() or entries[0].file_size > limit:
        raise InvalidMusicXmlError(
            "Save the compressed MusicXML with one score entry within the size limit."
        )
    with archive.open(entries[0]) as stream:
        content = stream.read(limit + 1)
    if len(content) > limit:
        raise InvalidMusicXmlError(
            "Save the compressed MusicXML with a score within the size limit."
        )
    return content


def compressed_musicxml_bytes(content: bytes) -> bytes:
    """Return the score document, without extracting files to the filesystem."""
    try:
        with ZipFile(BytesIO(content)) as archive:
            manifest = _read_entry(archive, CONTAINER, _MANIFEST_LIMIT)
            return _read_entry(archive, _rootfile(manifest), MAXIMUM_SIZE)
    except (BadZipFile, expat.ExpatError, NotImplementedError, RuntimeError, ValueError) as error:
        raise InvalidMusicXmlError("Save the score again as valid compressed MusicXML.") from error
