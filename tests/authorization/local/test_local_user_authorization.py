# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the authorization of personal mode."""

from uuid import uuid4

import pytest

from my_beautiful_choir.authorization.local.local_user_authorization import LocalUserAuthorization
from my_beautiful_choir.authorization.permission import Permission


@pytest.mark.parametrize("permission", list(Permission))
def test_everything_is_allowed(permission: Permission) -> None:
    authorization = LocalUserAuthorization()
    authorization.require(permission)
    authorization.require(permission, uuid4())
