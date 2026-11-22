# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Run the installed tools with separate arguments and bounded execution time."""

import shutil
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path

from scripts.installer.errors import InstallationError


def executable(name: str, path: str | None = None) -> Path:
    """Find an executable on the supplied or inherited PATH."""
    found = shutil.which(name, path=path)
    if found is None:
        raise InstallationError(f"{name} was not found. Install it or add it to PATH.")
    return Path(found).absolute()


def run_command(
    command: Sequence[str],
    *,
    failure: str,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    timeout: float = 30,
    missing_message: str | None = None,
) -> str | None:
    """Run a trusted local executable and keep its output available to the caller."""
    try:
        return subprocess.run(  # noqa: S603 - local tools found on PATH, no shell
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            check=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        ).stdout
    except subprocess.CalledProcessError as error:
        if error.returncode == 1 and missing_message and error.stderr.strip() == missing_message:
            return None
        raise InstallationError(failure) from error
    except (OSError, subprocess.SubprocessError) as error:
        raise InstallationError(failure) from error
