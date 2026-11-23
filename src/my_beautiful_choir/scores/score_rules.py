# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Rules of the attributes of a score."""

import re
import unicodedata
from uuid import UUID

from my_beautiful_choir.scores.errors import MEGABYTE, InvalidScoreError
from my_beautiful_choir.scores.formats.score_format import ScoreFormat

MAXIMUM_SIZE = 50 * MEGABYTE
LABEL_LENGTH = 100
ORIGINAL_NAME_LENGTH = 255

_CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")
_EXTENSION = re.compile(r"\.[A-Za-z][A-Za-z0-9]{0,4}$")
"""A trailing file extension: a dot, a letter, then at most four letters or digits."""
_SCORE_EXTENSION = re.compile(
    "(?:" + "|".join(re.escape(score_format.extension) for score_format in ScoreFormat) + ")$",
    re.IGNORECASE,
)
"""The extension of any score format, whatever its length or case (``.musicxml``)."""
_UNSAFE_NAME_CHARACTERS = re.compile(r'[\x00-\x1f\x7f<>:"/\\|?*]')
_RESERVED_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{digit}" for digit in range(1, 10)}
    | {f"LPT{digit}" for digit in range(1, 10)}
)
"""Names Windows reserves for devices, whatever their extension."""


def _clean(text: str) -> str:
    return unicodedata.normalize("NFC", _CONTROL_CHARACTERS.sub("", text)).strip()


def score_label(label: str | None, original_name: str, score_format: ScoreFormat) -> str:
    """Label of a new score: the one given, otherwise the original name without its extension.

    Raises:
        InvalidScoreError: if the given label is longer than ``LABEL_LENGTH``.
    """
    if label is not None:
        cleaned = _clean(label)
        if len(cleaned) > LABEL_LENGTH:
            raise InvalidScoreError("label", f"at most {LABEL_LENGTH} characters")
        if cleaned:
            return cleaned
    stem, dot, _ = original_name.rpartition(".")
    default = _clean(stem if dot and stem else original_name)[:LABEL_LENGTH].strip()
    return default or score_format.display_name


def original_name(name: str) -> str:
    """Original file name as recorded: without control characters, at most 255 characters."""
    return _clean(name)[:ORIGINAL_NAME_LENGTH]


def download_name(original: str, label: str, score_format: ScoreFormat) -> str:
    """File name proposed for a download of a score.

    It is the original name without its extension (the extension of a score
    format; otherwise a dot, a letter and at most four letters or digits,
    then a score format extension that this reveals), otherwise the label, with
    the characters that common file systems refuse replaced by ``_``, and
    always ends with the extension of the detected format. The original name
    stays unchanged in the score's metadata.
    """
    without_extension = _SCORE_EXTENSION.sub("", original)
    if without_extension == original:
        without_extension = _SCORE_EXTENSION.sub("", _EXTENSION.sub("", original))
    for name in (without_extension, label):
        stem = _UNSAFE_NAME_CHARACTERS.sub("_", name).strip(" .")
        if stem:
            break
    else:
        stem = "score"
    if stem.partition(".")[0].upper() in _RESERVED_NAMES:
        stem = f"_{stem}"
    stem = stem[: ORIGINAL_NAME_LENGTH - len(score_format.extension)].rstrip(" .") or "score"
    return stem + score_format.extension


def storage_key(choir_id: UUID, score_id: UUID) -> str:
    """Key of the content of a score in the file storage: ids only, never a user-given name."""
    return f"choirs/{choir_id}/scores/{score_id}"
