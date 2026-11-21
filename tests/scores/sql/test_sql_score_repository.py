# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Integration tests of the SQL score repository on a temporary SQLite file."""

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
        assert await unit_of_work.scores.get(score.id) == score


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
        assert await unit_of_work.scores.list(WORK.id) == [same_time, first, later]
        assert await unit_of_work.scores.list(uuid4()) == []


@pytest.mark.anyio
async def test_delete(database: SqlDatabase) -> None:
    kept, deleted = _score(), _score()
    await _add(database, kept, deleted)
    async with database.unit_of_work() as unit_of_work:
        await unit_of_work.scores.delete(deleted.id)
        await unit_of_work.commit()
    async with database.unit_of_work() as unit_of_work:
        assert await unit_of_work.scores.list(WORK.id) == [kept]


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
        assert await unit_of_work.scores.get(kept.id) == kept
        with pytest.raises(ScoreNotFoundError):
            await unit_of_work.scores.get(deleted.id)
