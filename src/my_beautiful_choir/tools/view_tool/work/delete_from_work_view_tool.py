# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Deletion initiated by the user in the Work view's confirmation dialog."""

from collections.abc import Mapping
from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.deletion.deleter import Deleter
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.view_tool.deletion.deletion_data import (
    DeletionStatus,
    deletion_data,
    describe_deletion_data,
)
from my_beautiful_choir.tools.view_tool.view_tool import ViewTool
from my_beautiful_choir.views.view import View


class DeleteFromWorkViewArguments(BaseModel):
    """Id of the item confirmed in the Work view."""

    target_id: UUID = Field(description="Id of the confirmed work or score.")


class DeleteFromWorkViewTool(ViewTool[DeleteFromWorkViewArguments]):
    """Carry out a deletion confirmed in the Work view."""

    def __init__(self, view: View, deleter: Deleter) -> None:
        super().__init__(view)
        self._deleter = deleter

    @property
    def name(self) -> str:
        return f"delete_{self._deleter.deletion_target.value}_from_view"

    @property
    def description(self) -> str:
        return "Carry out the deletion the user confirmed in the Work view."

    @property
    def arguments_model(self) -> type[DeleteFromWorkViewArguments]:
        return DeleteFromWorkViewArguments

    @property
    def app_only(self) -> bool:
        return True

    async def _collect(
        self, arguments: DeleteFromWorkViewArguments, context: ToolContext
    ) -> Mapping[str, object]:
        return deletion_data(
            DeletionStatus.DELETED, await self._deleter.delete(arguments.target_id)
        )

    def _describe(self, data: Mapping[str, object]) -> str:
        return describe_deletion_data(data)
