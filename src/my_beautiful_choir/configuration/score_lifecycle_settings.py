# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Personal-mode settings for confirmation and score PDF export."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class ScoreLifecycleSettings(BaseModel):
    """Capabilities to enable for this personal-mode installation."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    trusted_finalisation_host: bool = False
    musescore_executable: Path | None = None
    pdf_timeout_seconds: int = Field(default=60, ge=1, le=600)
