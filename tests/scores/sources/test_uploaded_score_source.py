# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the score sent by a view."""

import pytest

from my_beautiful_choir.errors import DomainError
from my_beautiful_choir.scores.errors import InvalidScoreSizeError
from my_beautiful_choir.scores.sources.score_content import ScoreContent
from my_beautiful_choir.scores.sources.uploaded_score_source import UploadedScoreSource


@pytest.mark.anyio
@pytest.mark.parametrize("content", [b"", b"12345"])
async def test_gives_the_received_content(content: bytes) -> None:
    fetched = await UploadedScoreSource("Ave Maria.pdf", content).fetch(limit=5)
    assert fetched == ScoreContent(original_name="Ave Maria.pdf", content=content)
    assert fetched.size == len(content)


@pytest.mark.anyio
async def test_content_over_the_limit_is_refused() -> None:
    with pytest.raises(InvalidScoreSizeError) as raised:
        await UploadedScoreSource("score.pdf", b"123456").fetch(limit=5)
    assert raised.value.limit == 5
    assert isinstance(raised.value, DomainError)


def test_the_size_error_states_the_limit_in_megabytes() -> None:
    assert str(InvalidScoreSizeError(50 * 1024 * 1024)) == (
        "The file is empty or too large: a score must hold between 1 byte and 50 MB."
    )
