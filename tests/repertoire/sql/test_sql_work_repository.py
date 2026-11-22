# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Integration tests of the SQL work repository on a temporary SQLite file."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from my_beautiful_choir.choirs.choir import Choir
from my_beautiful_choir.persistence.sql.sql_database import SqlDatabase
from my_beautiful_choir.repertoire.errors import WorkNotFoundError
from my_beautiful_choir.repertoire.work import Work, WorkDetails

NOW = datetime(2026, 11, 21, 12, 0, tzinfo=UTC)
CHOIR = Choir(uuid4(), "Chœur", NOW, is_default=True)
OTHER = Choir(uuid4(), "Ensemble", NOW, is_default=False)


@pytest.fixture
async def database(tmp_path: Path) -> SqlDatabase:
    database = SqlDatabase.in_directory(tmp_path)
    await database.migrate()
    async with database.unit_of_work() as unit_of_work:
        await unit_of_work.choirs.add(CHOIR)
        await unit_of_work.choirs.add(OTHER)
        await unit_of_work.commit()
    return database


def _work(title: str, composer: str | None = None, choir: Choir = CHOIR) -> Work:
    details = WorkDetails(
        title=title,
        composer=composer,
        arranger="Rutter",
        voicing="SATB",
        sung_languages=("la", "fr"),
        notes="Notes",
    )
    return Work(uuid4(), choir.id, details, NOW, NOW)


@pytest.mark.anyio
async def test_add_get_update_delete(database: SqlDatabase) -> None:
    work = _work("Ave María", "Bach")
    async with database.unit_of_work() as unit_of_work:
        await unit_of_work.works.add(work)
        assert await unit_of_work.works.get(work.id) == work
        edited = replace(
            work,
            details=replace(work.details, title="Ave verum", sung_languages=()),
            updated_at=NOW + timedelta(hours=1),
        )
        await unit_of_work.works.update(edited)
        assert await unit_of_work.works.get(work.id) == edited
        assert await unit_of_work.works.count(CHOIR.id) == 1
        await unit_of_work.works.delete(work.id)
        with pytest.raises(WorkNotFoundError):
            await unit_of_work.works.get(work.id)


@pytest.mark.anyio
async def test_search_ignores_case_and_accents(database: SqlDatabase) -> None:
    works = [
        _work("Ave María", "Bach"),
        _work("Ave verum", "Mozart"),
        _work("Signore", "Bédoù"),
        _work("100% joy_ful"),
        _work("Ave regina", choir=OTHER),
    ]
    async with database.unit_of_work() as unit_of_work:
        for work in works:
            await unit_of_work.works.add(work)

        async def titles(text: str | None) -> set[str]:
            return {w.title for w in await unit_of_work.works.search(CHOIR.id, text)}

        assert await titles(None) == {"Ave María", "Ave verum", "Signore", "100% joy_ful"}
        assert await titles("AVE MARIA") == {"Ave María"}
        assert await titles("bedou") == {"Signore"}
        assert await titles("%") == {"100% joy_ful"}
        assert await titles("y_f") == {"100% joy_ful"}
        assert await titles("") == {"Ave María", "Ave verum", "Signore", "100% joy_ful"}


@pytest.mark.anyio
async def test_deleting_a_choir_deletes_its_works(database: SqlDatabase) -> None:
    async with database.unit_of_work() as unit_of_work:
        await unit_of_work.works.add(_work("Ave regina", choir=OTHER))
        await unit_of_work.choirs.delete(OTHER.id)
        assert await unit_of_work.works.count(OTHER.id) == 0
