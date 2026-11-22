# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""App-only tool confirming a deletion kept pending by the "Deletion" view."""

from collections.abc import Mapping, Sequence

from pydantic import BaseModel, Field

from my_beautiful_choir.confirmation.pending_confirmations import PendingConfirmations
from my_beautiful_choir.deletion.deleter import Deleter
from my_beautiful_choir.deletion.deletion import Deletion
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.view_tool.deletion.deletion_data import (
    DeletionStatus,
    deletion_data,
    describe_deletion_data,
)
from my_beautiful_choir.tools.view_tool.view_tool import ViewTool
from my_beautiful_choir.views.view import View


class ConfirmDeletionArguments(BaseModel):
    """Arguments of ``confirm_deletion``."""

    token: str = Field(description="Token of the pending deletion, given to the view.")


class ConfirmDeletionTool(ViewTool[ConfirmDeletionArguments]):
    """Deletes what the user confirmed with the Delete button of the "Deletion" view.

    Hidden from the model: only the view calls it, when the user presses the
    button, so the model can never delete without a user action.
    """

    def __init__(
        self, view: View, deleters: Sequence[Deleter], pending: PendingConfirmations[Deletion]
    ) -> None:
        super().__init__(view)
        self._deleters = {deleter.deletion_target: deleter for deleter in deleters}
        self._pending = pending

    @property
    def name(self) -> str:
        """``confirm_deletion``."""
        return "confirm_deletion"

    @property
    def description(self) -> str:
        """Description for the host."""
        return "Carry out the deletion the user confirmed in the Deletion view."

    @property
    def app_only(self) -> bool:
        """Only the "Deletion" view calls it."""
        return True

    @property
    def arguments_model(self) -> type[ConfirmDeletionArguments]:
        """The token."""
        return ConfirmDeletionArguments

    async def _collect(
        self, arguments: ConfirmDeletionArguments, context: ToolContext
    ) -> Mapping[str, object]:
        pending = self._pending.take(arguments.token)
        deleted = await self._deleters[pending.target].delete(pending.target_id)
        return deletion_data(DeletionStatus.DELETED, deleted)

    def _describe(self, data: Mapping[str, object]) -> str:
        return describe_deletion_data(data)
