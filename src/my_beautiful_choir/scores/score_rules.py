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


def storage_key(choir_id: UUID, score_id: UUID) -> str:
    """Key of the content of a score in the file storage: ids only, never a user-given name."""
    return f"choirs/{choir_id}/scores/{score_id}"
