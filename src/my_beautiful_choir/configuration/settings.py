# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Settings of the application."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from my_beautiful_choir.configuration.data_dir import default_data_dir
from my_beautiful_choir.configuration.event_settings import EventSettings
from my_beautiful_choir.configuration.mode import Mode
from my_beautiful_choir.configuration.recognition_settings import RecognitionSettings
from my_beautiful_choir.configuration.score_lifecycle_settings import ScoreLifecycleSettings
from my_beautiful_choir.configuration.web_settings import WebSettings

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

ENV_PREFIX = "MBC_"
ENV_NESTED_DELIMITER = "__"


class Settings(BaseSettings):
    """Immutable, validated settings, read from ``MBC_``-prefixed environment variables."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        env_nested_delimiter=ENV_NESTED_DELIMITER,
        case_sensitive=False,
        env_ignore_empty=True,
        frozen=True,
        extra="ignore",
    )

    mode: Mode = Mode.PERSONAL
    log_level: LogLevel = "INFO"
    data_dir: Path = Field(default_factory=default_data_dir)
    web: WebSettings = Field(default_factory=WebSettings)
    recognition: RecognitionSettings = Field(default_factory=RecognitionSettings)
    score_lifecycle: ScoreLifecycleSettings = Field(default_factory=ScoreLifecycleSettings)
    events: EventSettings = Field(default_factory=EventSettings)
