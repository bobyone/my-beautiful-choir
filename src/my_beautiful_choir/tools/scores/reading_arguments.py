# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Arguments shared by paginated score inspections."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

Position = Annotated[int, Field(strict=True, ge=1, le=350_000)]
Label = Annotated[str, Field(strict=True, min_length=1, max_length=280)]
Selection = Position | Label


class ReadingArguments(BaseModel):
    """Continuation of the same operation with the same selection."""

    model_config = ConfigDict(hide_input_in_errors=True, extra="forbid")

    offset: int = Field(default=0, strict=True, ge=0, le=1_000_000)
    snapshot: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def require_snapshot_for_continuation(self) -> "ReadingArguments":
        """Avoid combining pages from different contents."""
        if self.offset and self.snapshot is None:
            raise ValueError("Use the snapshot returned with next_offset.")
        return self
