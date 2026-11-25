# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the settings of the events."""

import pytest
from pydantic import ValidationError

from my_beautiful_choir.configuration.event_settings import EventSettings


def test_defaults() -> None:
    settings = EventSettings()
    assert settings.default_period_days == 92
    assert settings.maximum_period_days == 366
    assert settings.notes_chars == 280


@pytest.mark.parametrize(
    "values",
    [
        {"default_period_days": 0},
        {"default_period_days": 367},
        {"maximum_period_days": 3661},
        {"notes_chars": 0},
        {"notes_chars": 2001},
        {"default_period_days": 30, "maximum_period_days": 29},
    ],
)
def test_invalid_values_are_refused(values: dict[str, int]) -> None:
    with pytest.raises(ValidationError):
        EventSettings.model_validate(values)
