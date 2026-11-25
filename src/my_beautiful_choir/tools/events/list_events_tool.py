# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tool listing the events of a choir over a period."""

from datetime import datetime

from pydantic import BaseModel, Field

from my_beautiful_choir.configuration.event_settings import EventSettings
from my_beautiful_choir.events.event_service import EventService
from my_beautiful_choir.tools.choirs.choir_data import CHOIR_FIELD_DESCRIPTION
from my_beautiful_choir.tools.events.event_data import (
    DATE_DESCRIPTION,
    UTC_NOTICE,
    event_data,
    event_label,
)
from my_beautiful_choir.tools.read_only_tool import ReadOnlyTool
from my_beautiful_choir.tools.tool_context import ToolContext
from my_beautiful_choir.tools.tool_result import ToolResult


class ListEventsArguments(BaseModel):
    """Arguments of ``list_events``."""

    choir: str | None = Field(default=None, description=CHOIR_FIELD_DESCRIPTION)
    start: datetime | None = Field(
        default=None, description=f"Start of the period, included. {DATE_DESCRIPTION}"
    )
    end: datetime | None = Field(
        default=None, description=f"End of the period, included. {DATE_DESCRIPTION}"
    )


class ListEventsTool(ReadOnlyTool[ListEventsArguments]):
    """Lists the events of a choir over a period, sorted by start."""

    def __init__(self, service: EventService, settings: EventSettings) -> None:
        self._service = service
        self._settings = settings

    @property
    def name(self) -> str:
        """``list_events``."""
        return "list_events"

    @property
    def description(self) -> str:
        """Description for the model."""
        default, maximum = self._settings.default_period_days, self._settings.maximum_period_days
        return (
            "List the events of a choir (concerts, rehearsals, lessons) that overlap a period, "
            f"sorted by start, with their ids. Without bounds, the period starts now and lasts "
            f"{default} days; with one bound, the other one is {default} days away. A period "
            f"lasts at most {maximum} days. {UTC_NOTICE}"
        )

    @property
    def arguments_model(self) -> type[ListEventsArguments]:
        """The choir and the period."""
        return ListEventsArguments

    async def execute(self, arguments: ListEventsArguments, context: ToolContext) -> ToolResult:
        """List the events."""
        listing = await self._service.list_events(arguments.choir, arguments.start, arguments.end)
        period = f"from {listing.period.start.isoformat()} to {listing.period.end.isoformat()}"
        if listing.events:
            lines = [f'Events of the choir "{listing.choir.name}" {period}:']
            lines.extend(
                f"- {event_label(seen.event)} (id {seen.event.id})" for seen in listing.events
            )
            text = "\n".join(lines)
        else:
            text = f'The choir "{listing.choir.name}" has no event {period}.'
        return ToolResult(
            text=text,
            structured={
                "choir": listing.choir.name,
                "period": {
                    "start": listing.period.start.isoformat(),
                    "end": listing.period.end.isoformat(),
                },
                "events": [event_data(seen, self._settings.notes_chars) for seen in listing.events],
            },
        )
