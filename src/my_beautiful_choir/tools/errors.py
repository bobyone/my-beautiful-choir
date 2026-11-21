# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Exceptions of the tools notion."""

from my_beautiful_choir.errors import DomainError, MyBeautifulChoirError


class ToolError(MyBeautifulChoirError):
    """Base class of the errors related to tools."""


class ToolExecutionError(ToolError, DomainError):
    """A tool could not complete; its message is shown to the model."""


class ToolCallSuspended(ToolError):  # noqa: N818 - control flow, not a failure
    """The call ends early, waiting for the user; the client calls the tool again.

    Not a failure: the transport adapter turns it into its own result.
    """
