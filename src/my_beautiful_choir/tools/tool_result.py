# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Result of a tool call."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from my_beautiful_choir.tools.tool_file import ToolFile


@dataclass(frozen=True)
class ToolResult:
    """Result of a tool call.

    Attributes:
        text: self-sufficient English text, for the model and for clients without views.
        structured: the same information as structured data, for the view.
        files: files given back to the client, after the text.
        png_images: images delivered as visual content to clients that support it.
    """

    text: str
    structured: Mapping[str, object] = field(default_factory=dict)
    files: Sequence[ToolFile] = ()
    png_images: Sequence[bytes] = ()
