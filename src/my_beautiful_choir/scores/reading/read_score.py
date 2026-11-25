# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""A musical snapshot and the stored score it describes."""

from dataclasses import dataclass

from my_beautiful_choir.scores.reading.score_music import ScoreMusic
from my_beautiful_choir.scores.score import Score


@dataclass(frozen=True)
class ReadScore:
    """Contents of a score with a fingerprint for consistent continuation."""

    score: Score
    music: ScoreMusic
    fingerprint: str
