# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Rules of choir names."""

import unicodedata

from my_beautiful_choir.choirs.errors import InvalidChoirNameError

MAXIMUM_LENGTH = 100


def clean_choir_name(name: str) -> str:
    """Return the name without surrounding spaces, in Unicode normal form C.

    Raises:
        InvalidChoirNameError: if it is empty or longer than the maximum length.
    """
    cleaned = unicodedata.normalize("NFC", name.strip())
    if not cleaned or len(cleaned) > MAXIMUM_LENGTH:
        raise InvalidChoirNameError(MAXIMUM_LENGTH)
    return cleaned


def choir_name_key(name: str) -> str:
    """Key comparing names ignoring case: two choirs never have the same key."""
    return unicodedata.normalize("NFC", name.strip()).casefold()
