# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Errors for visual access to a source score."""

from my_beautiful_choir.errors import DomainError


class PdfPageError(DomainError):
    """The requested PDF page could not be read."""
