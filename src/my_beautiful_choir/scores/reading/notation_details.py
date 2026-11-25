# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Traversal of musical details independently of their source format."""

from collections.abc import Iterable, Iterator

from my_beautiful_choir.scores.reading.notation import Notation


def walk_notation(details: Iterable[Notation]) -> Iterator[Notation]:
    """Visit every attached musical detail."""
    for detail in details:
        yield detail
        yield from walk_notation(detail.details)
