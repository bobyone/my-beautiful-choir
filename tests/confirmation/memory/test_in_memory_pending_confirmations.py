# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the pending confirmations kept in memory."""

from datetime import timedelta

import pytest

from my_beautiful_choir.confirmation.errors import ConfirmationExpiredError
from my_beautiful_choir.confirmation.memory.in_memory_pending_confirmations import (
    InMemoryPendingConfirmations,
)
from my_beautiful_choir.errors import DomainError
from tests.doubles import FakeClock


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


def test_a_token_gives_its_action_once(clock: FakeClock) -> None:
    pending = InMemoryPendingConfirmations[str](clock)
    first, second = pending.keep("delete A"), pending.keep("delete B")
    assert first != second
    assert len(first) >= 40
    assert pending.take(second) == "delete B"
    assert pending.take(first) == "delete A"
    with pytest.raises(ConfirmationExpiredError) as raised:
        pending.take(first)
    assert isinstance(raised.value, DomainError)
    assert "nothing was done" in str(raised.value)


def test_an_unknown_token_is_refused(clock: FakeClock) -> None:
    with pytest.raises(ConfirmationExpiredError):
        InMemoryPendingConfirmations[str](clock).take("guessed")


def test_a_token_expires_after_ten_minutes(clock: FakeClock) -> None:
    pending = InMemoryPendingConfirmations[str](clock)
    kept = pending.keep("delete A")
    still_valid = pending.keep("delete B")
    clock.advance(timedelta(minutes=9, seconds=59))
    assert pending.take(still_valid) == "delete B"
    clock.advance(timedelta(seconds=1))
    with pytest.raises(ConfirmationExpiredError):
        pending.take(kept)


def test_expired_actions_are_forgotten(clock: FakeClock) -> None:
    pending = InMemoryPendingConfirmations[str](clock, lifetime=timedelta(minutes=1))
    expired = pending.keep("delete A")
    clock.advance(timedelta(minutes=2))
    pending.keep("delete B")
    clock.current = clock.start
    with pytest.raises(ConfirmationExpiredError):
        pending.take(expired)
