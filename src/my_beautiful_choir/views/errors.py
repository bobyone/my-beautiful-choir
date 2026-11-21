# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Exceptions of the views notion."""

from typing import ClassVar

from my_beautiful_choir.errors import MyBeautifulChoirError, StartupError


class ViewError(MyBeautifulChoirError):
    """Base class of the errors related to views."""


class ViewNotFoundError(ViewError, StartupError):
    """The HTML document of a view is missing: the installation is incomplete."""

    error_code: ClassVar[str] = "MBC-INSTALL"
    exit_code: ClassVar[int] = 4

    def __init__(self, uri: str) -> None:
        super().__init__(
            message=f"the view {uri} is missing from the installation.",
            remedy=(
                "Reinstall my-beautiful-choir. When running from a clone of the repository, "
                "build the user interface first: uv run nox -s ui."
            ),
        )
        self.uri = uri
