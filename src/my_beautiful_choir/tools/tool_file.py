# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""File attached to the result of a tool call."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolFile:
    """A file given back to the client with the result of a tool.

    Attributes:
        name: file name proposed to the client; metadata only, never a path.
        media_type: media type of the content.
        content: bytes of the file.
    """

    name: str
    media_type: str
    content: bytes = field(repr=False)
