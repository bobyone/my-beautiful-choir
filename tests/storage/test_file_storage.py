# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the storage keys."""

import pytest

from my_beautiful_choir.storage.errors import InvalidStorageKeyError, StorageError
from my_beautiful_choir.storage.file_storage import check_storage_key


@pytest.mark.parametrize(
    "key",
    ["score", "choirs/0f8fad5b-d9cb-469f-a165-70867728950e/scores/7c9e6679", "a_b/C-1"],
)
def test_valid_keys_are_kept(key: str) -> None:
    assert check_storage_key(key) == key


@pytest.mark.parametrize(
    "key",
    [
        "",
        "/choirs",
        "choirs/",
        "choirs//scores",
        "../secret",
        "choirs/../../secret",
        "choirs\\scores",
        "C:/scores",
        "choirs/score.pdf",
        "chœurs",
        "choirs/ scores",
    ],
)
def test_invalid_keys_are_refused(key: str) -> None:
    with pytest.raises(InvalidStorageKeyError) as raised:
        check_storage_key(key)
    assert isinstance(raised.value, StorageError)
    assert isinstance(raised.value, ValueError)
    assert raised.value.key == key
