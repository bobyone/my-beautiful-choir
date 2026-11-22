# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Deletion preview requested by the Work view."""

from collections.abc import Mapping
from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.confirmation.pending_confirmations import PendingConfirmations
from my_beautiful_choir.deletion.deleter import Deleter
from my_beautiful_choir.deletion.deletion_preview import DeletionPreview
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.view_tool.deletion.deletion_data import (
    DeletionStatus,
    deletion_data,
    describe_deletion_data,
)
from my_beautiful_choir.tools.view_tool.view_tool import ViewTool
from my_beautiful_choir.views.view import View


class PreviewDeletionFromWorkViewArguments(BaseModel):
    """Id of the item selected in the Work view."""

    target_id: UUID = Field(description="Id of the selected work or score.")


class PreviewDeletionFromWorkViewTool(ViewTool[PreviewDeletionFromWorkViewArguments]):
    """Prepare a deletion preview for the Work view's confirmation dialog."""

    def __init__(
        self, view: View, deleter: Deleter, pending: PendingConfirmations[DeletionPreview]
    ) -> None:
        super().__init__(view)
        self._deleter = deleter
        self._pending = pending

    @property
    def name(self) -> str:
        return f"preview_{self._deleter.deletion_target.value}_deletion"

    @property
    def description(self) -> str:
        return "Prepare the deletion preview for the Work view."

    @property
    def arguments_model(self) -> type[PreviewDeletionFromWorkViewArguments]:
        return PreviewDeletionFromWorkViewArguments

    @property
    def app_only(self) -> bool:
        return True

    async def _collect(
        self, arguments: PreviewDeletionFromWorkViewArguments, context: ToolContext
    ) -> Mapping[str, object]:
        preview = await self._deleter.describe_deletion(arguments.target_id)
        return deletion_data(DeletionStatus.PENDING, preview.deletion, self._pending.keep(preview))

    def _describe(self, data: Mapping[str, object]) -> str:
        return describe_deletion_data(data)
