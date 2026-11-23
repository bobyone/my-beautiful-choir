# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the repertoire page bounds."""

import pytest

from my_beautiful_choir.repertoire.errors import InvalidRepertoirePageError
from my_beautiful_choir.repertoire.repertoire_page import (
    DEFAULT_PAGE_SIZE,
    MAXIMUM_PAGE_SIZE,
    PageRequest,
    page_count,
)


def test_default_request() -> None:
    assert PageRequest() == PageRequest(1, DEFAULT_PAGE_SIZE)
    assert DEFAULT_PAGE_SIZE == 10


@pytest.mark.parametrize(("number", "size"), [(0, 10), (1, 0), (1, MAXIMUM_PAGE_SIZE + 1)])
def test_out_of_bounds_request(number: int, size: int) -> None:
    with pytest.raises(InvalidRepertoirePageError):
        PageRequest(number, size)


@pytest.mark.parametrize(
    ("work_count", "size", "expected"), [(0, 10, 1), (1, 10, 1), (10, 10, 1), (11, 10, 2)]
)
def test_page_count(work_count: int, size: int, expected: int) -> None:
    assert page_count(work_count, size) == expected
