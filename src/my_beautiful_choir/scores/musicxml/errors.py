# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Errors for MusicXML exchanged as text."""

from my_beautiful_choir.errors import DomainError


class InvalidMusicXmlError(DomainError):
    """The payload is not a supported MusicXML score."""
