# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the deletion of works, with in-memory doubles."""

from uuid import uuid4

import pytest

from my_beautiful_choir.authorization.errors import AccessDeniedError
from my_beautiful_choir.authorization.permission import Permission
from my_beautiful_choir.deletion.deletion import Deletion, DeletionTarget
from my_beautiful_choir.repertoire.errors import WorkNotFoundError
from tests.doubles import DenyingAuthorization
from tests.repertoire_world import RepertoireWorld


@pytest.fixture
def world() -> RepertoireWorld:
    return RepertoireWorld()


@pytest.mark.anyio
async def test_describe_then_delete_a_work_with_its_scores(world: RepertoireWorld) -> None:
    await world.choir("Chœur")
    work = await world.work("Chœur", "Ave Maria")
    kept = await world.work("Chœur", "Requiem")
    await world.score(work, "Alto")
    await world.score(work, "Tenor")
    kept_score = await world.score(kept, "Alto")
    service = world.repertoire()
    assert service.deletion_target is DeletionTarget.WORK
    expected = Deletion(DeletionTarget.WORK, work.id, "Ave Maria", "Chœur", score_count=2)
    assert await service.describe_deletion(work.id) == expected
    assert len(world.storage.files) == 3
    assert await service.delete(work.id) == expected
    assert list(world.database.data.works) == [kept.id]
    assert list(world.database.data.scores) == [kept_score.id]
    assert list(world.storage.files) == [kept_score.storage_key]


@pytest.mark.anyio
async def test_a_missing_work(world: RepertoireWorld) -> None:
    with pytest.raises(WorkNotFoundError):
        await world.repertoire().describe_deletion(uuid4())
    with pytest.raises(WorkNotFoundError):
        await world.repertoire().delete(uuid4())


@pytest.mark.anyio
async def test_deleting_requires_the_right_to_manage_the_repertoire(
    world: RepertoireWorld,
) -> None:
    await world.choir("Chœur")
    work = await world.work("Chœur", "Ave Maria")
    denied = world.repertoire(DenyingAuthorization(Permission.MANAGE_REPERTOIRE))
    with pytest.raises(AccessDeniedError):
        await denied.describe_deletion(work.id)
    with pytest.raises(AccessDeniedError):
        await denied.delete(work.id)
    assert list(world.database.data.works) == [work.id]
