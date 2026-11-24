# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Launch description for a discovered Audiveris installation."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AudiverisLaunch:
    """A native executable or an installed Flatpak app and its launcher."""

    executable: Path
    flatpak_app_id: str | None = None

    def command(self, workspace: Path) -> tuple[str, ...]:
        """Build the launcher arguments and share only the job directory with Flatpak."""
        if self.flatpak_app_id is None:
            return (str(self.executable),)
        return (
            str(self.executable),
            "run",
            f"--filesystem={workspace}",
            self.flatpak_app_id,
        )
