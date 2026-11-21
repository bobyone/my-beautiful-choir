# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Exceptions of the tools notion."""

from my_beautiful_choir.errors import MyBeautifulChoirError


class ToolError(MyBeautifulChoirError):
    """Base class of the errors related to tools."""


class ToolExecutionError(ToolError):
    """A tool could not complete; its message is shown to the model."""
