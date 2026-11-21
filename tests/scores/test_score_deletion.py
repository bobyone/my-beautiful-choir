# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the deletion of scores, with in-memory doubles."""

from uuid import uuid4

import pytest

from my_beautiful_choir.authorization.errors import AccessDeniedError
from my_beautiful_choir.authorization.permission import Permission
from my_beautiful_choir.deletion.deletion import Deletion, DeletionTarget
from my_beautiful_choir.scores.errors import ScoreNotFoundError
from tests.doubles import DenyingAuthorization
from tests.repertoire_world import RepertoireWorld


@pytest.fixture
def world() -> RepertoireWorld:
    return RepertoireWorld()


@pytest.mark.anyio
async def test_describe_then_delete_a_score_and_its_content(world: RepertoireWorld) -> None:
    await world.choir("Chœur")
    work = await world.work("Chœur", "Ave Maria")
    score = await world.score(work, "Alto")
    kept = await world.score(work, "Tenor")
    service = world.scores()
    assert service.deletion_target is DeletionTarget.SCORE
    expected = Deletion(DeletionTarget.SCORE, score.id, "Alto", "Ave Maria")
    assert await service.describe_deletion(score.id) == expected
    assert len(world.storage.files) == 2
    assert await service.delete(score.id) == expected
    assert await service.list_scores(work.id) == [kept]
    assert list(world.storage.files) == [kept.storage_key]


@pytest.mark.anyio
async def test_a_missing_score(world: RepertoireWorld) -> None:
    with pytest.raises(ScoreNotFoundError):
        await world.scores().describe_deletion(uuid4())
    with pytest.raises(ScoreNotFoundError):
        await world.scores().delete(uuid4())


@pytest.mark.anyio
async def test_deleting_requires_the_right_to_manage_the_repertoire(
    world: RepertoireWorld,
) -> None:
    await world.choir("Chœur")
    work = await world.work("Chœur", "Ave Maria")
    score = await world.score(work, "Alto")
    denied = world.scores(DenyingAuthorization(Permission.MANAGE_REPERTOIRE))
    with pytest.raises(AccessDeniedError):
        await denied.describe_deletion(score.id)
    with pytest.raises(AccessDeniedError):
        await denied.delete(score.id)
    assert list(world.storage.files) == [score.storage_key]
