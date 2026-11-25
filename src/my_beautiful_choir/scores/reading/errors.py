# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Errors of reading and comparing scores."""

from my_beautiful_choir.scores.errors import ScoresError


class ScoreReadingError(ScoresError):
    """The score cannot be read into musical content."""


class ScoreSelectionError(ScoresError):
    """A part, measure or continuation could not be selected."""


class ScoreComparisonError(ScoresError):
    """The two scores or the requested matches cannot be compared."""
