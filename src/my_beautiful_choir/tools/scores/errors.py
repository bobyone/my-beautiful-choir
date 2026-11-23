# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Exceptions of the score tools."""

from my_beautiful_choir.scores.errors import MEGABYTE
from my_beautiful_choir.tools.errors import ToolExecutionError


class ScoreTooLargeToReturnError(ToolExecutionError):
    """A score is too large to be returned in the conversation."""

    def __init__(self, label: str, limit: int) -> None:
        super().__init__(
            f"The score {label!r} is too large to be returned in the conversation: at most "
            f"{limit / MEGABYTE:g} MB. Open it on the user's computer with open_score, or "
            "let the user download it with Download in the Work view (show_work)."
        )
        self.label = label
        self.limit = limit
