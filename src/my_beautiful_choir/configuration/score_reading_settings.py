# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Limits for musical inspection responses in personal mode."""

from pydantic import BaseModel, ConfigDict, Field


class ScoreReadingSettings(BaseModel):
    """Free-text limits by field and total character budget per result page."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    label_chars: int = Field(default=280, ge=1, le=2_000)
    lyric_chars: int = Field(default=280, ge=1, le=2_000)
    direction_chars: int = Field(default=280, ge=1, le=2_000)
    other_text_chars: int = Field(default=280, ge=1, le=2_000)
    page_chars: int = Field(default=12_000, ge=1_000, le=12_000)
