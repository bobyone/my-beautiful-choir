# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool deleting a choir with its works and scores."""

from uuid import UUID

from pydantic import BaseModel, Field

from my_beautiful_choir.choirs.choir_service import ChoirService
from my_beautiful_choir.confirmation.pending_confirmations import PendingConfirmations
from my_beautiful_choir.deletion.deletion_preview import DeletionPreview
from my_beautiful_choir.tools.view_tool.deletion.delete_tool import DeleteTool
from my_beautiful_choir.views.view import View


class DeleteChoirArguments(BaseModel):
    """Arguments of ``delete_choir``."""

    choir: str = Field(description="Exact name of the choir to delete, ignoring case.")


class DeleteChoirTool(DeleteTool[DeleteChoirArguments]):
    """Deletes a choir after the user's confirmation."""

    def __init__(
        self,
        view: View,
        service: ChoirService,
        pending: PendingConfirmations[DeletionPreview],
        conversation: PendingConfirmations[tuple[str, DeletionPreview]],
    ) -> None:
        super().__init__(view, service, pending, conversation)
        self._service = service

    @property
    def name(self) -> str:
        """``delete_choir``."""
        return "delete_choir"

    @property
    def description(self) -> str:
        """Description for the model."""
        return (
            "Delete a choir with all its works and scores, after the user's confirmation, "
            "which this tool asks for itself: never ask for it in the conversation first. "
            "If it was the default choir, the oldest remaining choir becomes the default one."
        )

    @property
    def arguments_model(self) -> type[DeleteChoirArguments]:
        """The choir."""
        return DeleteChoirArguments

    async def _target_id(self, arguments: DeleteChoirArguments) -> UUID:
        return (await self._service.get_choir(arguments.choir)).id
