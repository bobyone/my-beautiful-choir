# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Typed details of written notation independent of its interchange format."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Notation:
    """A recognised musical detail and its attached details."""

    kind: str
    value: str = ""
    properties: tuple[tuple[str, str], ...] = ()
    details: tuple["Notation", ...] = ()
