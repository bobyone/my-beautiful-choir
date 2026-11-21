# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Exceptions of the transport notion."""

from typing import ClassVar

from my_beautiful_choir.errors import MyBeautifulChoirError, StartupError


class TransportError(MyBeautifulChoirError):
    """Base class of the errors related to transports."""


class PortUnavailableError(TransportError, StartupError):
    """The HTTP port cannot be listened on."""

    error_code: ClassVar[str] = "MBC-PORT"
    exit_code: ClassVar[int] = 3

    def __init__(self, host: str, port: int, reason: str) -> None:
        super().__init__(
            message=f"cannot listen on {host}:{port}: {reason}.",
            remedy=(
                "Stop the program using this port, or choose another one with MBC_WEB__PORT, "
                "then restart."
            ),
        )
        self.host = host
        self.port = port
