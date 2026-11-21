# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""View abstraction."""

from abc import ABC, abstractmethod


class View(ABC):
    """A user interface rendered by the MCP client, identified by a ``ui://`` URI."""

    @property
    @abstractmethod
    def uri(self) -> str:
        """The ``ui://`` URI of the view."""

    @abstractmethod
    def content(self) -> str:
        """The self-contained HTML document of the view.

        Raises:
            ViewNotFoundError: if the view is not available.
        """
