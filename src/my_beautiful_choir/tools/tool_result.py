# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Result of a tool call."""

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolResult:
    """Result of a tool call.

    Attributes:
        text: self-sufficient English text, for the model and for clients without views.
        structured: the same information as structured data, for the view.
    """

    text: str
    structured: Mapping[str, object] = field(default_factory=dict)
