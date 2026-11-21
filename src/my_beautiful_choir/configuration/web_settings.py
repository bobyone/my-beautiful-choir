# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Settings specific to web mode."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import NoDecode


class WebSettings(BaseModel):
    """HTTP listening settings of web mode."""

    model_config = ConfigDict(frozen=True)

    host: Annotated[str, Field(min_length=1)] = "127.0.0.1"
    port: Annotated[int, Field(ge=1, le=65535)] = 9000
    allowed_hosts: Annotated[tuple[str, ...], NoDecode] = ()

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def _split_allowed_hosts(cls, value: object) -> object:
        """Accept a comma-separated list, as given by an environment variable."""
        if isinstance(value, str):
            return tuple(item.strip() for item in value.split(",") if item.strip())
        return value
