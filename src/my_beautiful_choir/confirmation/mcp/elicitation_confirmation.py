# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Confirmation asked through MCP elicitation, on every protocol version."""

import logging

from mcp.server.elicitation import AcceptedElicitation, render_elicitation_schema
from mcp.server.mcpserver import Context
from mcp.types import (
    ElicitRequest,
    ElicitRequestFormParams,
    ElicitResult,
    InputRequiredResult,
)
from pydantic import BaseModel, Field, ValidationError

from my_beautiful_choir.confirmation.confirmation_outcome import ConfirmationOutcome
from my_beautiful_choir.confirmation.confirmation_requester import ConfirmationRequester
from my_beautiful_choir.tools.errors import ToolCallSuspended

_LOGGER = logging.getLogger(__name__)

INPUT_KEY = "confirmation"
"""Key of the confirmation in the input requests and responses of a call."""

MULTI_ROUND_TRIP_PROTOCOL = "2026-07-28"
"""First protocol version where a server asks the client by ending the call (SEP-2322)."""


class ConfirmationAnswer(BaseModel):
    """Form shown to the user by the MCP client."""

    confirmed: bool = Field(default=True, title="Confirm", description="Check to confirm.")


class ConfirmationInputRequired(ToolCallSuspended):
    """Ends the call with a confirmation request; the client retries it with the answer."""

    def __init__(self, result: InputRequiredResult) -> None:
        super().__init__("The user's confirmation is required")
        self.result = result


def _outcome_of(answer: ElicitResult) -> ConfirmationOutcome:
    if answer.action != "accept":
        return ConfirmationOutcome.REFUSED
    try:
        confirmed = ConfirmationAnswer.model_validate(answer.content or {}).confirmed
    except ValidationError:
        return ConfirmationOutcome.REFUSED
    return ConfirmationOutcome.CONFIRMED if confirmed else ConfirmationOutcome.REFUSED


class ElicitationConfirmation(ConfirmationRequester):
    """Asks the user through the MCP client (elicitation), when the client supports it.

    - From protocol 2026-07-28, the call ends with an input request
      (``ConfirmationInputRequired``) and the client retries it with the
      answer, which is read on the retry: the tool runs twice.
    - Before, the question is asked during the call.
    """

    def __init__(self, context: Context) -> None:
        self._context = context

    async def ask(self, question: str) -> ConfirmationOutcome:
        """Confirmed only when the user accepts the form with the box checked."""
        answer = (self._context.input_responses or {}).get(INPUT_KEY)
        if isinstance(answer, ElicitResult):
            return _outcome_of(answer)
        capabilities = self._context.client_capabilities
        if capabilities is None or capabilities.elicitation is None:
            return ConfirmationOutcome.UNAVAILABLE
        if (self._context.protocol_version or "") >= MULTI_ROUND_TRIP_PROTOCOL:
            raise ConfirmationInputRequired(self._input_request(question))
        return await self._ask_during_the_call(question)

    async def _ask_during_the_call(self, question: str) -> ConfirmationOutcome:
        try:
            result = await self._context.elicit(question, ConfirmationAnswer)
        except ValueError:
            # Accepted with an answer that does not match the form.
            return ConfirmationOutcome.REFUSED
        except Exception:
            _LOGGER.warning("The confirmation could not be asked", exc_info=True)
            return ConfirmationOutcome.UNAVAILABLE
        if isinstance(result, AcceptedElicitation) and result.data.confirmed:
            return ConfirmationOutcome.CONFIRMED
        return ConfirmationOutcome.REFUSED

    @staticmethod
    def _input_request(question: str) -> InputRequiredResult:
        request = ElicitRequest(
            params=ElicitRequestFormParams(
                message=question,
                requested_schema=render_elicitation_schema(ConfirmationAnswer),
            )
        )
        return InputRequiredResult(input_requests={INPUT_KEY: request})
