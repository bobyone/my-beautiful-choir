# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""View whose HTML document is built ahead of time and packaged."""

from importlib.resources import files
from importlib.resources.abc import Traversable

from my_beautiful_choir.views.errors import ViewNotFoundError
from my_beautiful_choir.views.view import View

URI_PREFIX = "ui://my-beautiful-choir/"


def packaged_views_directory() -> Traversable:
    """Directory of the built views inside the installed package."""
    return files("my_beautiful_choir.views.static")


class PackagedView(View):
    """Reads ``<name>.html`` from a directory once, then keeps it in memory.

    Args:
        name: file name of the view, without extension; also the last part of its URI.
        directory: directory holding the built views.
    """

    def __init__(self, name: str, directory: Traversable) -> None:
        self._name = name
        self._directory = directory
        self._content: str | None = None

    @property
    def uri(self) -> str:
        """``ui://my-beautiful-choir/<name>.html``."""
        return f"{URI_PREFIX}{self._name}.html"

    def content(self) -> str:
        """Return the HTML document, read on first use.

        Raises:
            ViewNotFoundError: if the file is missing.
        """
        if self._content is None:
            document = self._directory.joinpath(f"{self._name}.html")
            if not document.is_file():
                raise ViewNotFoundError(self.uri)
            self._content = document.read_text(encoding="utf-8")
        return self._content
