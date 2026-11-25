# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Settings of the events."""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EventSettings(BaseModel):
    """Limits of the events.

    The period used to list events has a default and a maximum length, in days.
    Notes are free text returned to the model: they are bounded by ``notes_chars``
    (280 by default, the free-text limit given to the model), and longer stored
    notes are withheld from the model.
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    default_period_days: int = Field(default=92, ge=1, le=366)
    maximum_period_days: int = Field(default=366, ge=1, le=3660)
    notes_chars: int = Field(default=280, ge=1, le=2_000)

    @model_validator(mode="after")
    def _default_within_maximum(self) -> Self:
        if self.default_period_days > self.maximum_period_days:
            raise ValueError("default_period_days must not exceed maximum_period_days")
        return self
