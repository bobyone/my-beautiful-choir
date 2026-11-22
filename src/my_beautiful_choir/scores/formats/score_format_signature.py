# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Score format signature abstraction."""

from abc import ABC, abstractmethod

from my_beautiful_choir.scores.formats.score_format import ScoreFormat


class ScoreFormatSignature(ABC):
    """Recognizes one score format from the content of a file, never from its name.

    A signature never decompresses an archive nor parses XML: it only looks at
    the bytes, or at the index of a zip archive.
    """

    @property
    @abstractmethod
    def format(self) -> ScoreFormat:
        """Format this signature recognizes."""

    @abstractmethod
    def matches(self, content: bytes) -> bool:
        """Whether ``content`` is a file of this format."""
