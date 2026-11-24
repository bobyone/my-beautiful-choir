# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Configuration of local score recognition."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class RecognitionSettings(BaseModel):
    """Settings injected into the personal-mode recognizer."""

    model_config = ConfigDict(frozen=True)
    audiveris_executable: Path | None = None
    timeout_seconds: int = Field(default=600, ge=1, le=3600)
