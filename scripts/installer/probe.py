# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Verify personal-mode startup through the MCP SDK using an isolated data directory."""

import sys
from collections.abc import Sequence
from tempfile import TemporaryDirectory

import anyio
from mcp.client import Client
from mcp.client.stdio import StdioServerParameters

from scripts.installer.client import SERVER_NAME
from scripts.installer.errors import InstallationError

PROBE_TIMEOUT_SECONDS = 30


async def verify_launcher(launcher: Sequence[str]) -> None:
    """Start the registered command, initialize MCP, and call show_about."""
    command, *args = launcher
    with TemporaryDirectory(prefix="mbc-install-check-") as directory:
        server = StdioServerParameters(command=command, args=args, env={"MBC_DATA_DIR": directory})
        with anyio.fail_after(PROBE_TIMEOUT_SECONDS):
            async with Client(server) as client:
                result = await client.call_tool("show_about", {})
                data = result.structured_content
                if (
                    result.is_error
                    or data is None
                    or data.get("name") != SERVER_NAME
                    or data.get("mode") != "personal"
                ):
                    raise InstallationError("The server did not identify itself in personal mode.")


if __name__ == "__main__":
    anyio.run(verify_launcher, sys.argv[1:])
