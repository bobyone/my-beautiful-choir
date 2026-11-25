# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""The draft and content presented to the user before finalisation."""

from dataclasses import dataclass

from my_beautiful_choir.scores.score import Score


@dataclass(frozen=True)
class FinalisationPreview:
    """A snapshot of the score and a digest of its validated contents."""

    score: Score
    content_digest: bytes
