# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Context of a tool call."""

from dataclasses import dataclass

from my_beautiful_choir.confirmation.confirmation_requester import ConfirmationRequester


@dataclass(frozen=True)
class ToolContext:
    """What a tool can use during one call, besides its arguments."""

    confirmation: ConfirmationRequester
    """Asks the user to confirm an action during this call."""
    client_shows_views: bool = False
    """Whether the client declared that it shows views (MCP Apps) for this call.

    Such a client keeps app-only tools away from the model; any other client
    may let the model call them.
    """
