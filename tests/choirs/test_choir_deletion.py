# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the deletion of choirs, with in-memory doubles."""

from uuid import uuid4

import pytest

from my_beautiful_choir.authorization.errors import AccessDeniedError
from my_beautiful_choir.authorization.permission import Permission
from my_beautiful_choir.choirs.errors import ChoirNotFoundError
from my_beautiful_choir.deletion.deletion import Deletion, DeletionTarget
from tests.doubles import DenyingAuthorization
from tests.repertoire_world import RepertoireWorld


@pytest.fixture
def world() -> RepertoireWorld:
    return RepertoireWorld()


@pytest.mark.anyio
async def test_describe_counts_the_works_and_scores_and_changes_nothing(
    world: RepertoireWorld,
) -> None:
    choir = await world.choir("Chœur")
    first = await world.work("Chœur", "Ave Maria")
    await world.work("Chœur", "Requiem")
    await world.score(first, "Alto")
    await world.score(first, "Tenor")
    service = world.choirs()
    assert service.deletion_target is DeletionTarget.CHOIR
    assert await service.describe_deletion(choir.id) == Deletion(
        DeletionTarget.CHOIR, choir.id, "Chœur", work_count=2, score_count=2
    )
    assert len(world.database.data.works) == 2
    assert len(world.storage.files) == 2


@pytest.mark.anyio
async def test_delete_removes_the_works_scores_and_stored_contents(world: RepertoireWorld) -> None:
    choir = await world.choir("Chœur")
    kept_choir = await world.choir("Ensemble")
    work = await world.work("Chœur", "Ave Maria")
    kept_work = await world.work("Ensemble", "Gloria")
    await world.score(work, "Alto")
    kept_score = await world.score(kept_work, "Alto")
    deleted = await world.choirs().delete(choir.id)
    assert deleted.work_count == 1
    assert deleted.score_count == 1
    assert list(world.database.data.choirs) == [kept_choir.id]
    assert list(world.database.data.works) == [kept_work.id]
    assert list(world.database.data.scores) == [kept_score.id]
    assert list(world.storage.files) == [kept_score.storage_key]


@pytest.mark.anyio
async def test_deleting_the_default_choir_makes_the_oldest_remaining_one_default(
    world: RepertoireWorld,
) -> None:
    default = await world.choir("Chœur")
    oldest = await world.choir("Ensemble")
    await world.choir("Schola")
    await world.choirs().delete(default.id)
    choirs = await world.choirs().list_choirs()
    assert [(choir.name, choir.is_default) for choir in choirs] == [
        ("Ensemble", True),
        ("Schola", False),
    ]
    assert choirs[0].id == oldest.id


@pytest.mark.anyio
async def test_deleting_another_choir_keeps_the_default_one(world: RepertoireWorld) -> None:
    await world.choir("Chœur")
    other = await world.choir("Ensemble")
    await world.choirs().delete(other.id)
    assert [(c.name, c.is_default) for c in await world.choirs().list_choirs()] == [("Chœur", True)]


@pytest.mark.anyio
async def test_deleting_the_last_choir_leaves_none(world: RepertoireWorld) -> None:
    choir = await world.choir("Chœur")
    await world.choirs().delete(choir.id)
    assert await world.choirs().list_choirs() == []


@pytest.mark.anyio
async def test_a_missing_choir(world: RepertoireWorld) -> None:
    with pytest.raises(ChoirNotFoundError):
        await world.choirs().describe_deletion(uuid4())
    with pytest.raises(ChoirNotFoundError):
        await world.choirs().delete(uuid4())


@pytest.mark.anyio
async def test_get_choir_by_name(world: RepertoireWorld) -> None:
    choir = await world.choir("Chœur")
    assert await world.choirs().get_choir("CHŒUR") == choir
    with pytest.raises(ChoirNotFoundError):
        await world.choirs().get_choir("Ensemble")
    denied = world.choirs(DenyingAuthorization(Permission.CONSULT_REPERTOIRE))
    with pytest.raises(AccessDeniedError):
        await denied.get_choir("Chœur")


@pytest.mark.anyio
async def test_deleting_requires_the_right_to_manage_choirs(world: RepertoireWorld) -> None:
    choir = await world.choir("Chœur")
    denied = world.choirs(DenyingAuthorization(Permission.MANAGE_CHOIRS))
    with pytest.raises(AccessDeniedError):
        await denied.describe_deletion(choir.id)
    with pytest.raises(AccessDeniedError):
        await denied.delete(choir.id)
    assert list(world.database.data.choirs) == [choir.id]
