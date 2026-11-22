# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Command shared by the two local MCP registrations."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Launcher:
    """Absolute paths to uv and the checkout that owns the installation."""

    uv: Path
    checkout: Path

    @property
    def command(self) -> tuple[str, ...]:
        """Start personal mode with the already prepared project environment."""
        return (
            str(self.uv),
            "run",
            "--frozen",
            "--no-sync",
            "--directory",
            str(self.checkout),
            "my-beautiful-choir",
            "--mode",
            "personal",
        )
