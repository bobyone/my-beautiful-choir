# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Integration tests of the SQL score repository on a temporary SQLite file."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from my_beautiful_choir.choirs.choir import Choir
from my_beautiful_choir.persistence.sql.sql_database import SqlDatabase
from my_beautiful_choir.repertoire.work import Work, WorkDetails
from my_beautiful_choir.scores.errors import ScoreNotFoundError
from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.score import Score
from my_beautiful_choir.scores.score_origin import ScoreOrigin
from my_beautiful_choir.scores.score_rules import storage_key
from my_beautiful_choir.scores.score_state import ScoreState

NOW = datetime(2026, 11, 21, 12, 0, tzinfo=UTC)
CHOIR = Choir(uuid4(), "Chœur", NOW, is_default=True)
OTHER = Choir(uuid4(), "Ensemble", NOW, is_default=False)
WORK = Work(uuid4(), CHOIR.id, WorkDetails(title="Ave Maria"), NOW, NOW)
SECOND_WORK = Work(uuid4(), CHOIR.id, WorkDetails(title="Requiem"), NOW, NOW)
OTHER_WORK = Work(uuid4(), OTHER.id, WorkDetails(title="Gloria"), NOW, NOW)


@pytest.fixture
async def database(tmp_path: Path) -> SqlDatabase:
    database = SqlDatabase.in_directory(tmp_path)
    await database.migrate()
    async with database.unit_of_work() as unit_of_work:
        for choir in (CHOIR, OTHER):
            await unit_of_work.choirs.add(choir)
        for work in (WORK, SECOND_WORK, OTHER_WORK):
            await unit_of_work.works.add(work)
        await unit_of_work.commit()
    return database


def _score(
    work: Work = WORK, label: str = "Alto part", added_at: datetime = NOW, link: str | None = None
) -> Score:
    score_id = uuid4()
    return Score(
        id=score_id,
        work_id=work.id,
        label=label,
        format=ScoreFormat.COMPRESSED_MUSICXML,
        size=1234,
        original_name="Ave Maria.mxl",
        origin=ScoreOrigin.GOOGLE_DRIVE if link else ScoreOrigin.LOCAL_FILE,
        link=link,
        storage_key=storage_key(work.choir_id, score_id),
        added_at=added_at,
    )


async def _add(database: SqlDatabase, *scores: Score) -> None:
    async with database.unit_of_work() as unit_of_work:
        for score in scores:
            await unit_of_work.scores.add(score)
        await unit_of_work.commit()


@pytest.mark.anyio
async def test_add_and_get(database: SqlDatabase) -> None:
    score = _score(link="https://drive.google.com/file/d/abcdefghijkl/view")
    await _add(database, score)
    async with database.unit_of_work() as unit_of_work:
        assert await unit_of_work.scores.get(score.id) == replace(score, version_number=1)


@pytest.mark.anyio
async def test_concurrent_finalisations_allocate_distinct_versions(database: SqlDatabase) -> None:
    original = _score()
    first_draft = replace(_score(), state=ScoreState.DRAFT, draft_revision=1)
    second_draft = replace(_score(), state=ScoreState.DRAFT, draft_revision=1)
    await _add(database, original, first_draft, second_draft)
    async with database.unit_of_work() as unit:
        await unit.scores.delete(original.id)
        await unit.commit()

    async def finalise(draft: Score) -> Score:
        async with database.unit_of_work() as unit:
            await unit.start_snapshot(for_update=True)
            final = await unit.scores.finalise(draft)
            await unit.commit()
        return final

    finals = await asyncio.gather(finalise(first_draft), finalise(second_draft))
    assert {score.version_number for score in finals} == {2, 3}
    assert all(score.state is ScoreState.FINAL for score in finals)
    async with database.unit_of_work() as unit:
        assert {score.version_number for score in await unit.scores.list(WORK.id)} == {2, 3}


@pytest.mark.anyio
async def test_get_a_missing_score(database: SqlDatabase) -> None:
    async with database.unit_of_work() as unit_of_work:
        with pytest.raises(ScoreNotFoundError):
            await unit_of_work.scores.get(uuid4())


@pytest.mark.anyio
async def test_list_the_scores_of_a_work_the_oldest_first(database: SqlDatabase) -> None:
    later = _score(label="Alto", added_at=NOW + timedelta(minutes=1))
    first = _score(label="Tenor")
    same_time = _score(label="Bass")
    await _add(database, later, first, same_time, _score(SECOND_WORK))
    async with database.unit_of_work() as unit_of_work:
        assert await unit_of_work.scores.list(WORK.id) == [
            replace(same_time, version_number=3),
            replace(first, version_number=2),
            replace(later, version_number=1),
        ]
        assert await unit_of_work.scores.list(uuid4()) == []


@pytest.mark.anyio
async def test_delete(database: SqlDatabase) -> None:
    kept, deleted = _score(), _score()
    await _add(database, kept, deleted)
    async with database.unit_of_work() as unit_of_work:
        await unit_of_work.scores.delete(deleted.id)
        await unit_of_work.commit()
    async with database.unit_of_work() as unit_of_work:
        assert await unit_of_work.scores.list(WORK.id) == [replace(kept, version_number=1)]


@pytest.mark.anyio
async def test_storage_keys_of_a_work_and_a_choir(database: SqlDatabase) -> None:
    first, second, other = _score(), _score(SECOND_WORK), _score(OTHER_WORK)
    await _add(database, first, second, other)
    async with database.unit_of_work() as unit_of_work:
        assert await unit_of_work.scores.storage_keys_of_work(WORK.id) == [first.storage_key]
        assert sorted(await unit_of_work.scores.storage_keys_of_choir(CHOIR.id)) == sorted(
            [first.storage_key, second.storage_key]
        )
        assert await unit_of_work.scores.storage_keys_of_choir(OTHER.id) == [other.storage_key]
        counts = await unit_of_work.scores.counts_of_works([WORK.id, SECOND_WORK.id])
        assert counts == {WORK.id: 1, SECOND_WORK.id: 1}
        assert await unit_of_work.scores.counts_of_works({OTHER_WORK.id}) == {OTHER_WORK.id: 1}
        assert await unit_of_work.scores.counts_of_works([uuid4()]) == {}
        assert await unit_of_work.scores.counts_of_works([]) == {}


@pytest.mark.anyio
async def test_deleting_a_work_deletes_its_scores(database: SqlDatabase) -> None:
    score = _score()
    await _add(database, score)
    async with database.unit_of_work() as unit_of_work:
        await unit_of_work.works.delete(WORK.id)
        await unit_of_work.commit()
    async with database.unit_of_work() as unit_of_work:
        with pytest.raises(ScoreNotFoundError):
            await unit_of_work.scores.get(score.id)


@pytest.mark.anyio
async def test_a_score_needs_an_existing_work(database: SqlDatabase) -> None:
    orphan = _score(Work(UUID(int=1), CHOIR.id, WorkDetails(title="Missing"), NOW, NOW))
    with pytest.raises(IntegrityError):
        await _add(database, orphan)


@pytest.mark.anyio
async def test_deleting_a_choir_deletes_the_scores_of_its_works(database: SqlDatabase) -> None:
    deleted, kept = _score(), _score(OTHER_WORK)
    await _add(database, deleted, kept)
    async with database.unit_of_work() as unit_of_work:
        await unit_of_work.choirs.delete(CHOIR.id)
        await unit_of_work.commit()
    async with database.unit_of_work() as unit_of_work:
        assert await unit_of_work.scores.storage_keys_of_choir(CHOIR.id) == []
        assert await unit_of_work.scores.get(kept.id) == replace(kept, version_number=1)
        with pytest.raises(ScoreNotFoundError):
            await unit_of_work.scores.get(deleted.id)
