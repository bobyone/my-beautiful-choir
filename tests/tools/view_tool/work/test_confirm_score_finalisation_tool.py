# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the Work view confirmation boundary."""

from dataclasses import replace

import pytest

from my_beautiful_choir.confirmation.memory.in_memory_pending_confirmations import (
    InMemoryPendingConfirmations,
)
from my_beautiful_choir.scores.finalisation_preview import FinalisationPreview
from my_beautiful_choir.scores.score_origin import ScoreOrigin
from my_beautiful_choir.scores.score_state import ScoreState
from my_beautiful_choir.tools.view_tool.work.confirm_score_finalisation_tool import (
    ConfirmScoreFinalisationArguments,
    ConfirmScoreFinalisationTool,
)
from tests import score_samples
from tests.doubles import StubView, tool_context
from tests.repertoire_world import RepertoireWorld
from tests.score_doubles import StubScoreSource


@pytest.mark.anyio
async def test_rejects_confirmation_from_a_different_session() -> None:
    world = RepertoireWorld()
    choir = await world.choir("Choir")
    work = await world.work(choir.name, "Song")
    scores = world.scores()
    _, draft = await scores.add_score(
        work.id, StubScoreSource(score_samples.musicxml(), origin=ScoreOrigin.MUSICXML_TEXT)
    )
    _, preview = await scores.preview_finalisation(draft.id)
    assert preview is not None

    pending = InMemoryPendingConfirmations[tuple[object, FinalisationPreview]](world.clock)
    issuing_context = replace(tool_context(), session=object())
    other_context = replace(tool_context(), session=object())
    token = pending.keep((issuing_context.session, preview))
    tool = ConfirmScoreFinalisationTool(StubView(), scores, pending)

    result = await tool.execute(ConfirmScoreFinalisationArguments(token=token), other_context)

    assert result.structured == {"finalisation_stale": True}
    assert draft.state is ScoreState.DRAFT
    assert (await scores.describe_score(draft.id))[1] == draft
