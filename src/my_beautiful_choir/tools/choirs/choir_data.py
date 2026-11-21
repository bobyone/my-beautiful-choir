# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Structured content and descriptions shared by the choir tools."""

from collections.abc import Mapping

from my_beautiful_choir.choirs.choir import Choir

CHOIR_FIELD_DESCRIPTION = (
    "Exact name of an existing choir, ignoring case. Omit it to use the default choir."
)


def choir_data(choir: Choir) -> Mapping[str, object]:
    """Structured content describing a choir."""
    return {"name": choir.name, "is_default": choir.is_default}


def choir_label(choir: Choir) -> str:
    """Name of the choir, marked when it is the default one."""
    return f"{choir.name} (default)" if choir.is_default else choir.name
