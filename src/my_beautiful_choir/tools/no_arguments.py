# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Arguments of a tool that takes none."""

from pydantic import BaseModel, ConfigDict


class NoArguments(BaseModel):
    """Empty arguments model."""

    model_config = ConfigDict(frozen=True, extra="forbid")
