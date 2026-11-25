# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the observer of personal mode."""

from uuid import uuid4

from my_beautiful_choir.authorization.local.local_observer_source import LocalObserverSource
from my_beautiful_choir.authorization.observer import LOCAL_USER
from my_beautiful_choir.authorization.observer_kind import ObserverKind


def test_the_local_user_observes_every_choir() -> None:
    source = LocalObserverSource()

    observer = source.observer(uuid4())

    assert observer == LOCAL_USER
    assert observer.kind is ObserverKind.LOCAL_USER
    assert observer.member_id is None
