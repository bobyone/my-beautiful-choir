# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Exceptions of the choirs notion."""

from my_beautiful_choir.errors import DomainError


class ChoirError(DomainError):
    """Base class of the errors related to choirs."""


class ChoirNotFoundError(ChoirError):
    """No choir has the given name or id."""

    def __init__(self, choir: str) -> None:
        super().__init__(f"No choir is named {choir!r}. List the choirs to find its exact name.")
        self.choir = choir


class NoChoirError(ChoirError):
    """No choir exists yet."""

    def __init__(self) -> None:
        super().__init__(
            "No choir exists yet. Ask the user for the name of their first choir, then create it."
        )


class InvalidChoirNameError(ChoirError):
    """The name is empty or too long."""

    def __init__(self, maximum_length: int) -> None:
        super().__init__(f"A choir name must contain between 1 and {maximum_length} characters.")


class ChoirNameTakenError(ChoirError):
    """Another choir already has this name."""

    def __init__(self, name: str) -> None:
        super().__init__(f"A choir named {name!r} already exists. Choose another name.")
        self.name = name
