# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool deleting an element once the user confirmed it."""

from abc import abstractmethod
from collections.abc import Mapping
from uuid import UUID

from pydantic import BaseModel

from my_beautiful_choir.confirmation.confirmation_outcome import ConfirmationOutcome
from my_beautiful_choir.confirmation.pending_confirmations import PendingConfirmations
from my_beautiful_choir.deletion.deleter import Deleter
from my_beautiful_choir.deletion.deletion import Deletion
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.view_tool.deletion.deletion_data import (
    DeletionStatus,
    deletion_data,
    deletion_question,
    describe_deletion_data,
)
from my_beautiful_choir.tools.view_tool.view_tool import ViewTool
from my_beautiful_choir.views.view import View


class DeleteTool[ArgumentsT: BaseModel](ViewTool[ArgumentsT]):
    """Template method: find the element, ask the user, then delete or keep it pending.

    Nothing changes before the question: from protocol 2026-07-28 the tool
    runs twice, once to ask and once with the answer (ADR 0013).

    - Confirmed: the element is deleted.
    - Refused: nothing is deleted.
    - The user cannot be asked: the deletion is kept under a token, and the
      "Deletion" view shows it with a button that confirms it.
    """

    def __init__(
        self, view: View, deleter: Deleter, pending: PendingConfirmations[Deletion]
    ) -> None:
        super().__init__(view)
        self._deleter = deleter
        self._pending = pending

    @abstractmethod
    async def _target_id(self, arguments: ArgumentsT) -> UUID:
        """Id of the element named by the arguments.

        Raises:
            DomainError: if there is no such element.
        """

    async def _collect(self, arguments: ArgumentsT, context: ToolContext) -> Mapping[str, object]:
        deletion = await self._deleter.describe_deletion(await self._target_id(arguments))
        match await context.confirmation.ask(deletion_question(deletion)):
            case ConfirmationOutcome.CONFIRMED:
                deleted = await self._deleter.delete(deletion.target_id)
                return deletion_data(DeletionStatus.DELETED, deleted)
            case ConfirmationOutcome.REFUSED:
                return deletion_data(DeletionStatus.REFUSED, deletion)
            case ConfirmationOutcome.UNAVAILABLE:
                token = self._pending.keep(deletion)
                return deletion_data(DeletionStatus.PENDING, deletion, token)

    def _describe(self, data: Mapping[str, object]) -> str:
        return describe_deletion_data(data)
