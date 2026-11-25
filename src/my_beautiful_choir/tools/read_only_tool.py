# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool contract for operations that never modify the repertoire."""

from abc import ABC

from pydantic import BaseModel

from my_beautiful_choir.tools.tool import Tool


class ReadOnlyTool[ArgumentsT: BaseModel](Tool[ArgumentsT], ABC):
    """Publish a tool as read-only."""

    @property
    def read_only(self) -> bool:
        return True
