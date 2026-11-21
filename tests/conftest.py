# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Shared test configuration."""

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Run asynchronous tests (marked ``anyio``) on asyncio only."""
    return "asyncio"
