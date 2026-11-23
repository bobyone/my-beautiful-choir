# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Integration test of the repertoire pages on a temporary SQLite file."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from my_beautiful_choir.authorization.local.local_user_authorization import LocalUserAuthorization
from my_beautiful_choir.choirs.choir import Choir
from my_beautiful_choir.persistence.sql.sql_database import SqlDatabase
from my_beautiful_choir.repertoire.page_request import PageRequest
from my_beautiful_choir.repertoire.repertoire_service import RepertoireService
from my_beautiful_choir.repertoire.work import Work, WorkDetails
from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.score import Score
from my_beautiful_choir.scores.score_origin import ScoreOrigin
from my_beautiful_choir.scores.score_rules import storage_key
from tests.doubles import FakeClock
from tests.score_doubles import InMemoryFileStorage

NOW = datetime(2026, 11, 23, 12, 0, tzinfo=UTC)
CHOIR = Choir(uuid4(), "Chœur", NOW, is_default=True)
OTHER = Choir(uuid4(), "Ensemble", NOW, is_default=False)


def _score(work: Work) -> Score:
    score_id = uuid4()
    return Score(
        id=score_id,
        work_id=work.id,
        label=f"Part {score_id.hex[:6]}",
        format=ScoreFormat.PDF,
        size=10,
        original_name="part.pdf",
        origin=ScoreOrigin.LOCAL_FILE,
        link=None,
        storage_key=storage_key(work.choir_id, score_id),
        added_at=NOW,
    )


@pytest.fixture
async def service(tmp_path: Path) -> RepertoireService:
    database = SqlDatabase.in_directory(tmp_path)
    await database.migrate()
    works = {
        title: Work(uuid4(), CHOIR.id, WorkDetails(title=title), NOW, NOW)
        for title in ["Echo", "alpha", "Delta", "Bravo", "Charlie"]
    }
    other = Work(uuid4(), OTHER.id, WorkDetails(title="Alpha"), NOW, NOW)
    async with database.unit_of_work() as unit_of_work:
        for choir in (CHOIR, OTHER):
            await unit_of_work.choirs.add(choir)
        for work in [*works.values(), other]:
            await unit_of_work.works.add(work)
        for work, count in [(works["Bravo"], 2), (works["Charlie"], 1), (other, 3)]:
            for _ in range(count):
                await unit_of_work.scores.add(_score(work))
        await unit_of_work.commit()
    return RepertoireService(
        database.unit_of_work, FakeClock(), LocalUserAuthorization(), InMemoryFileStorage()
    )


@pytest.mark.anyio
async def test_pages_with_score_counts(service: RepertoireService) -> None:
    first = await service.search_page_with_score_counts(None, None, PageRequest(1, 2))
    assert first.choir == CHOIR
    assert [(w.title, first.score_counts[w.id]) for w in first.works] == [
        ("alpha", 0),
        ("Bravo", 2),
    ]
    assert (first.number, first.work_count, first.page_count) == (1, 5, 3)

    second = await service.search_page_with_score_counts(None, None, PageRequest(2, 2))
    assert [(w.title, second.score_counts[w.id]) for w in second.works] == [
        ("Charlie", 1),
        ("Delta", 0),
    ]
    assert set(second.score_counts) == {w.id for w in second.works}

    last = await service.search_page_with_score_counts(None, None, PageRequest(7, 2))
    assert ([w.title for w in last.works], last.number) == (["Echo"], 3)

    found = await service.search_page_with_score_counts(None, "A", PageRequest(2, 2))
    assert [w.title for w in found.works] == ["Charlie", "Delta"]
    assert (found.work_count, found.page_count) == (4, 2)
    other = await service.search_page_with_score_counts("Ensemble", "alp", PageRequest())
    assert [(w.title, other.score_counts[w.id]) for w in other.works] == [("Alpha", 3)]
