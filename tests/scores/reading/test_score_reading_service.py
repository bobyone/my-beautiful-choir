# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Check shared work and authorisation before reading source contents."""

from unittest.mock import create_autospec
from uuid import uuid4

import pytest

from my_beautiful_choir.authorization.errors import AccessDeniedError
from my_beautiful_choir.authorization.permission import Permission
from my_beautiful_choir.scores.reading.score_reader import ScoreReader
from my_beautiful_choir.scores.reading.score_reading_service import ScoreReadingService
from my_beautiful_choir.scores.score_service import ScoreService
from tests.repertoire_world import RepertoireWorld


@pytest.mark.anyio
async def test_checks_access_to_both_scores_before_reading_either_file() -> None:
    world = RepertoireWorld()
    choir = await world.choir("Choir")
    work = await world.work(choir.name, "Song")
    before = await world.score(work, "Before")
    scores = create_autospec(ScoreService, instance=True)
    reader = create_autospec(ScoreReader, instance=True)
    scores.describe_score.side_effect = (
        (work, before),
        AccessDeniedError(Permission.CONSULT_REPERTOIRE, choir.id),
    )
    with pytest.raises(AccessDeniedError):
        await ScoreReadingService(scores, reader).read_pair(before.id, uuid4())
    scores.read_score.assert_not_awaited()
    reader.read.assert_not_awaited()
