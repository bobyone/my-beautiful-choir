# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the choir service, with in-memory doubles."""

from datetime import timedelta

import pytest

from my_beautiful_choir.authorization.errors import AccessDeniedError
from my_beautiful_choir.authorization.local.local_user_authorization import LocalUserAuthorization
from my_beautiful_choir.authorization.permission import Permission
from my_beautiful_choir.choirs.choir_service import ChoirService, find_choir
from my_beautiful_choir.choirs.errors import (
    ChoirNameTakenError,
    ChoirNotFoundError,
    InvalidChoirNameError,
    NoChoirError,
)
from tests.doubles import DenyingAuthorization, FakeClock
from tests.persistence_doubles import InMemoryDatabase


@pytest.fixture
def database() -> InMemoryDatabase:
    return InMemoryDatabase()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def service(database: InMemoryDatabase, clock: FakeClock) -> ChoirService:
    return ChoirService(database.unit_of_work, clock, LocalUserAuthorization())


async def _create(service: ChoirService, clock: FakeClock, *names: str) -> None:
    for name in names:
        await service.create(name)
        clock.advance(timedelta(minutes=1))


@pytest.mark.anyio
async def test_the_first_choir_becomes_the_default_one(
    service: ChoirService, clock: FakeClock
) -> None:
    first = await service.create("  Chœur de Lyon ")
    clock.advance(timedelta(minutes=1))
    second = await service.create("Ensemble vocal")
    assert (first.name, first.is_default, first.created_at) == ("Chœur de Lyon", True, clock.start)
    assert second.is_default is False
    assert [c.name for c in await service.list_choirs()] == ["Chœur de Lyon", "Ensemble vocal"]


@pytest.mark.anyio
@pytest.mark.parametrize("name", ["", "   ", "x" * 101])
async def test_invalid_names_are_refused(service: ChoirService, name: str) -> None:
    with pytest.raises(InvalidChoirNameError, match="between 1 and 100"):
        await service.create(name)


@pytest.mark.anyio
async def test_names_are_unique_ignoring_case(service: ChoirService) -> None:
    await service.create("Chœur de Lyon")
    with pytest.raises(ChoirNameTakenError):
        await service.create("CHŒUR DE LYON")


@pytest.mark.anyio
async def test_rename(service: ChoirService, clock: FakeClock) -> None:
    await _create(service, clock, "Chœur", "Ensemble")
    renamed = await service.rename("chœur", "Chœur de Lyon")
    assert (renamed.name, renamed.is_default) == ("Chœur de Lyon", True)
    assert [c.name for c in await service.list_choirs()] == ["Chœur de Lyon", "Ensemble"]


@pytest.mark.anyio
async def test_rename_changing_only_the_case(service: ChoirService) -> None:
    await service.create("choeur")
    assert (await service.rename("choeur", "Choeur")).name == "Choeur"


@pytest.mark.anyio
async def test_rename_to_the_name_of_another_choir_is_refused(
    service: ChoirService, clock: FakeClock
) -> None:
    await _create(service, clock, "Chœur", "Ensemble")
    with pytest.raises(ChoirNameTakenError):
        await service.rename("Chœur", "ensemble")


@pytest.mark.anyio
async def test_rename_unknown_choir(service: ChoirService) -> None:
    with pytest.raises(ChoirNotFoundError, match="'Absent'"):
        await service.rename("Absent", "Other")


@pytest.mark.anyio
async def test_set_default(service: ChoirService, clock: FakeClock) -> None:
    await _create(service, clock, "Chœur", "Ensemble")
    chosen = await service.set_default("ENSEMBLE")
    assert chosen.is_default
    assert [(c.name, c.is_default) for c in await service.list_choirs()] == [
        ("Chœur", False),
        ("Ensemble", True),
    ]


@pytest.mark.anyio
async def test_find_choir_by_name_or_default(
    service: ChoirService, database: InMemoryDatabase, clock: FakeClock
) -> None:
    async with database.unit_of_work() as unit_of_work:
        with pytest.raises(NoChoirError):
            await find_choir(unit_of_work.choirs, None)
    await _create(service, clock, "Chœur", "Ensemble")
    async with database.unit_of_work() as unit_of_work:
        assert (await find_choir(unit_of_work.choirs, None)).name == "Chœur"
        assert (await find_choir(unit_of_work.choirs, "ensemble")).name == "Ensemble"


@pytest.mark.anyio
async def test_failed_operations_change_nothing(
    service: ChoirService, database: InMemoryDatabase
) -> None:
    await service.create("Chœur")
    commits = database.commits
    with pytest.raises(ChoirNameTakenError):
        await service.create("chœur")
    assert database.commits == commits


@pytest.mark.anyio
async def test_permissions_are_required(database: InMemoryDatabase, clock: FakeClock) -> None:
    allowed = ChoirService(database.unit_of_work, clock, LocalUserAuthorization())
    await allowed.create("Chœur")
    denied = ChoirService(database.unit_of_work, clock, DenyingAuthorization(*Permission))
    for operation in (
        denied.list_choirs(),
        denied.create("Ensemble"),
        denied.rename("Chœur", "Ensemble"),
        denied.set_default("Chœur"),
    ):
        with pytest.raises(AccessDeniedError):
            await operation
