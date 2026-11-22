# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the deletion of works, with in-memory doubles."""

from uuid import uuid4

import pytest

from my_beautiful_choir.authorization.errors import AccessDeniedError
from my_beautiful_choir.authorization.permission import Permission
from my_beautiful_choir.deletion.deletion import Deletion, DeletionTarget
from my_beautiful_choir.deletion.deletion_preview import DeletionPreview
from my_beautiful_choir.deletion.stale_confirmation_error import StaleConfirmationError
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
    preview = await service.describe_deletion(work.id)
    assert preview.deletion == expected
    assert len(world.storage.files) == 3
    assert await service.delete(preview) == expected
    assert list(world.database.data.works) == [kept.id]
    assert list(world.database.data.scores) == [kept_score.id]
    assert list(world.storage.files) == [kept_score.storage_key]


@pytest.mark.anyio
async def test_a_missing_work(world: RepertoireWorld) -> None:
    with pytest.raises(WorkNotFoundError):
        await world.repertoire().describe_deletion(uuid4())
    missing = DeletionPreview(Deletion(DeletionTarget.WORK, uuid4(), "Missing"))
    with pytest.raises(WorkNotFoundError):
        await world.repertoire().delete(missing)


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
        await denied.delete(await world.repertoire().describe_deletion(work.id))
    assert list(world.database.data.works) == [work.id]


@pytest.mark.anyio
@pytest.mark.parametrize("change", ["added", "removed", "replaced"])
async def test_an_original_preview_cannot_delete_changed_scores(
    world: RepertoireWorld, change: str
) -> None:
    await world.choir("Choir")
    work = await world.work("Choir", "Ave Maria")
    original = await world.score(work, "Alto")
    repertoire = world.repertoire()
    scores = world.scores()
    preview = await repertoire.describe_deletion(work.id)

    if change != "added":
        await scores.delete(await scores.describe_deletion(original.id))
    if change != "removed":
        await world.score(work, "Alto 2")

    current = await scores.list_scores(work.id)
    contents = world.storage.files.copy()
    assert len(current) == {"added": 2, "removed": 0, "replaced": 1}[change]
    with pytest.raises(StaleConfirmationError) as stale:
        await repertoire.delete(preview)

    assert await scores.list_scores(work.id) == current
    assert world.storage.files == contents
    assert stale.value.preview == await repertoire.describe_deletion(work.id)
    await repertoire.delete(stale.value.preview)
    assert not world.storage.files
