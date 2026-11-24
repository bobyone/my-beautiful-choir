# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the repertoire service, with in-memory doubles."""

from datetime import timedelta
from uuid import uuid4

import pytest

from my_beautiful_choir.authorization.errors import AccessDeniedError
from my_beautiful_choir.authorization.local.local_user_authorization import LocalUserAuthorization
from my_beautiful_choir.authorization.permission import Permission
from my_beautiful_choir.choirs.choir_service import ChoirService
from my_beautiful_choir.choirs.errors import ChoirNotFoundError, NoChoirError
from my_beautiful_choir.repertoire.errors import InvalidWorkError, WorkNotFoundError
from my_beautiful_choir.repertoire.page_request import PageRequest
from my_beautiful_choir.repertoire.repertoire_service import RepertoireService
from my_beautiful_choir.repertoire.work import WorkChanges, WorkDetails
from tests.doubles import DenyingAuthorization, FakeClock
from tests.persistence_doubles import InMemoryDatabase
from tests.score_doubles import InMemoryFileStorage


@pytest.fixture
def database() -> InMemoryDatabase:
    return InMemoryDatabase()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def service(database: InMemoryDatabase, clock: FakeClock) -> RepertoireService:
    return RepertoireService(
        database.unit_of_work, clock, LocalUserAuthorization(), InMemoryFileStorage()
    )


@pytest.fixture
async def choirs(database: InMemoryDatabase, clock: FakeClock) -> ChoirService:
    choirs = ChoirService(
        database.unit_of_work, clock, LocalUserAuthorization(), InMemoryFileStorage()
    )
    await choirs.create("Chœur")
    await choirs.create("Ensemble")
    return choirs


@pytest.mark.anyio
async def test_add_to_the_default_or_a_named_choir(
    service: RepertoireService, choirs: ChoirService
) -> None:
    choir, work = await service.add_work(None, WorkDetails(title=" Ave Maria ", composer="Bach"))
    assert choir.name == "Chœur"
    assert work.title == "Ave Maria"
    assert work.created_at == work.updated_at
    other, _ = await service.add_work("ensemble", WorkDetails(title="Ave Maria"))
    assert other.name == "Ensemble"


@pytest.mark.anyio
async def test_add_without_choir(service: RepertoireService) -> None:
    with pytest.raises(NoChoirError):
        await service.add_work(None, WorkDetails(title="Ave Maria"))


@pytest.mark.anyio
async def test_add_to_an_unknown_choir(service: RepertoireService, choirs: ChoirService) -> None:
    with pytest.raises(ChoirNotFoundError):
        await service.add_work("Absent", WorkDetails(title="Ave Maria"))


@pytest.mark.anyio
async def test_invalid_work_is_not_added(
    service: RepertoireService, choirs: ChoirService, database: InMemoryDatabase
) -> None:
    with pytest.raises(InvalidWorkError):
        await service.add_work(None, WorkDetails(title=""))
    assert database.data.works == {}


@pytest.mark.anyio
async def test_edit_changes_only_the_given_attributes(
    service: RepertoireService, choirs: ChoirService, clock: FakeClock
) -> None:
    _, work = await service.add_work(None, WorkDetails(title="Ave Maria", composer="Bach"))
    clock.advance(timedelta(hours=1))
    edited = await service.edit_work(work.id, WorkChanges(voicing="SATB"))
    assert edited.details == WorkDetails(title="Ave Maria", composer="Bach", voicing="SATB")
    assert edited.updated_at == work.created_at + timedelta(hours=1)
    choir, found = await service.get_work(work.id)
    assert (choir.name, found) == ("Chœur", edited)


@pytest.mark.anyio
async def test_unknown_work(service: RepertoireService) -> None:
    with pytest.raises(WorkNotFoundError):
        await service.edit_work(uuid4(), WorkChanges(title="x"))
    with pytest.raises(WorkNotFoundError):
        await service.get_work(uuid4())


@pytest.mark.anyio
async def test_search_in_title_and_composer(
    service: RepertoireService, choirs: ChoirService
) -> None:
    for title, composer in [("Ave María", "Bach"), ("Ave verum", "Mozart"), ("Signore", "Bédoù")]:
        await service.add_work(None, WorkDetails(title=title, composer=composer))
    await service.add_work("Ensemble", WorkDetails(title="Ave regina"))
    choir, every = await service.search(None)
    assert choir.name == "Chœur"
    assert len(every) == 3
    assert {w.title for w in (await service.search(None, "AVE MARIA"))[1]} == {"Ave María"}
    assert {w.title for w in (await service.search(None, "bedou"))[1]} == {"Signore"}
    assert {w.title for w in (await service.search("Ensemble", "ave"))[1]} == {"Ave regina"}


@pytest.mark.anyio
async def test_permissions_are_required(
    database: InMemoryDatabase, clock: FakeClock, service: RepertoireService, choirs: ChoirService
) -> None:
    _, work = await service.add_work(None, WorkDetails(title="Ave Maria"))
    managing = RepertoireService(
        database.unit_of_work,
        clock,
        DenyingAuthorization(Permission.MANAGE_REPERTOIRE),
        InMemoryFileStorage(),
    )
    with pytest.raises(AccessDeniedError):
        await managing.add_work(None, WorkDetails(title="x"))
    with pytest.raises(AccessDeniedError):
        await managing.edit_work(work.id, WorkChanges(title="x"))
    assert (await managing.search(None))[1] == [work]
    consulting = RepertoireService(
        database.unit_of_work,
        clock,
        DenyingAuthorization(Permission.CONSULT_REPERTOIRE),
        InMemoryFileStorage(),
    )
    with pytest.raises(AccessDeniedError):
        await consulting.search(None)
    with pytest.raises(AccessDeniedError):
        await consulting.search_titles(None, work.title, reference=False)
    with pytest.raises(AccessDeniedError):
        await consulting.get_work(work.id)


@pytest.mark.anyio
async def test_search_page_with_score_counts(
    service: RepertoireService, choirs: ChoirService, database: InMemoryDatabase
) -> None:
    for title in ["Delta", "alpha", "Écho", "Bravo", "Charlie"]:
        await service.add_work(None, WorkDetails(title=title))
    await service.add_work("Ensemble", WorkDetails(title="Alpha"))
    first = await service.search_page_with_score_counts(None, None, PageRequest(1, 2))
    assert first.choir.name == "Chœur"
    assert [w.title for w in first.works] == ["alpha", "Bravo"]
    assert (first.number, first.size, first.work_count, first.page_count) == (1, 2, 5, 3)
    assert first.score_counts == {w.id: 0 for w in first.works}
    last = await service.search_page_with_score_counts(None, None, PageRequest(9, 2))
    assert ([w.title for w in last.works], last.number) == (["Écho"], 3)
    found = await service.search_page_with_score_counts(None, "ECHO", PageRequest())
    assert ([w.title for w in found.works], found.page_count) == (["Écho"], 1)
    empty = await service.search_page_with_score_counts(None, "absent", PageRequest(4))
    assert (empty.works, empty.number, empty.work_count, empty.page_count) == ((), 1, 0, 1)
