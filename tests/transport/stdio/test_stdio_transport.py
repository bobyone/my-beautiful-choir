# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Unit tests of the stdio transport (the end-to-end test runs a real process)."""

from unittest.mock import AsyncMock

import pytest

from my_beautiful_choir.transport.stdio.stdio_transport import StdioTransport


@pytest.mark.anyio
async def test_serves_the_server_over_stdio() -> None:
    server = AsyncMock()
    await StdioTransport().run(server)
    server.run_stdio_async.assert_awaited_once_with()
