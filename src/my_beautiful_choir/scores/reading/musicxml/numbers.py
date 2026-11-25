# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Bounded exact values from MusicXML."""

import re
from fractions import Fraction

from my_beautiful_choir.scores.reading.errors import ScoreReadingError

_DECIMAL = re.compile(r"[+-]?(?:[0-9]{1,24}(?:\.[0-9]{0,12})?|\.[0-9]{1,12})")


def decimal(value: str | None) -> Fraction:
    """Read a bounded decimal without converting through a binary float."""
    if value is None or _DECIMAL.fullmatch(value.strip()) is None:
        raise ScoreReadingError("The score contains an invalid or oversized musical number.")
    return Fraction(value.strip())


def integer(value: str | None) -> int:
    """Read a whole musical number."""
    number = decimal(value)
    if number.denominator != 1:
        raise ScoreReadingError("The score contains an invalid whole musical number.")
    return number.numerator
