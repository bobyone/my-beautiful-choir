# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Build and verify a checkout before requesting any registration change."""

import logging
import os
from collections.abc import Callable, Mapping
from pathlib import Path

from scripts.installer.client import ClientRegistration
from scripts.installer.errors import InstallationError
from scripts.installer.launcher import Launcher
from scripts.installer.process import executable, run_command

_LOGGER = logging.getLogger(__name__)
BUILD_TIMEOUT_SECONDS = 15 * 60


def install(
    checkout: Path,
    client: ClientRegistration,
    confirm_replace: Callable[[], bool],
    environment: Mapping[str, str],
    *,
    node_dir: Path | None = None,
) -> None:
    """Prepare the checkout, probe the launcher and register it in the selected client."""
    if not (checkout / "uv.lock").is_file() or not (checkout / "noxfile.py").is_file():
        raise InstallationError("Run the installer from a complete my-beautiful-choir checkout.")
    launcher = Launcher(executable("uv", environment.get("PATH")), checkout)
    build_environment = dict(environment)
    if node_dir is not None:
        build_environment["PATH"] = os.pathsep.join(
            (str(node_dir.resolve()), environment.get("PATH", ""))
        )
    executable("node", build_environment.get("PATH"))
    executable("npm", build_environment.get("PATH"))

    uv = str(launcher.uv)
    _LOGGER.info("Preparing the Python environment.")
    run_command(
        [uv, "sync", "--frozen", "--extra", "personal-ocr"],
        cwd=checkout,
        env=build_environment,
        timeout=BUILD_TIMEOUT_SECONDS,
        failure="Python setup failed. Check uv, then run 'uv sync --frozen' for details.",
    )
    _LOGGER.info("Building the interface.")
    run_command(
        [uv, "run", "--frozen", "--no-sync", "nox", "-s", "ui"],
        cwd=checkout,
        env=build_environment,
        timeout=BUILD_TIMEOUT_SECONDS,
        failure="The interface build failed. Check Node.js and run 'uv run --frozen nox -s ui'.",
    )
    _LOGGER.info("Verifying the MCP server with temporary data.")
    run_command(
        [
            uv,
            "run",
            "--frozen",
            "--no-sync",
            "python",
            "-m",
            "scripts.installer.probe",
            *launcher.command,
        ],
        cwd=checkout,
        env=build_environment,
        timeout=60,
        failure="MCP startup verification failed. See the startup troubleshooting guide.",
    )
    client.register(launcher, confirm_replace)
