# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Content of a score fetched from a source."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreContent:
    """Bytes of a score file and its original file name.

    The original name is metadata only: it is never used as a path.
    """

    original_name: str
    content: bytes

    @property
    def size(self) -> int:
        """Size of the content, in bytes."""
        return len(self.content)
