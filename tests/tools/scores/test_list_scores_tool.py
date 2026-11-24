# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the view-free score listing tool with injected services."""

from unittest.mock import create_autospec
from uuid import uuid4

import pytest
from pydantic import ValidationError

from my_beautiful_choir.repertoire.repertoire_service import RepertoireService
from my_beautiful_choir.repertoire.work import Work, WorkDetails
from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.tools.scores.list_scores_tool import ListScoresArguments, ListScoresTool
from tests.doubles import FakeClock, tool_context


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"work_id": str(uuid4()), "work_title": "Adeste fideles"},
        {"work_title": "Adeste fideles", "work_reference": "NL15.2"},
        {"work_id": str(uuid4()), "choir": "Lyon"},
        {"work_title": "  "},
        {"work_reference": "  "},
    ],
)
def test_requires_exactly_one_nonblank_work_selector(arguments: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        ListScoresArguments.model_validate(arguments)


@pytest.mark.anyio
async def test_resolves_reference_then_lists_scores() -> None:
    repertoire = create_autospec(RepertoireService, instance=True)
    scores = create_autospec(ScoreService, instance=True)
    now = FakeClock().now()
    work = Work(uuid4(), uuid4(), WorkDetails("Adeste fideles (NL15.2)"), now, now)
    repertoire.search_titles.return_value = [work]
    scores.list_scores.return_value = []
    tool = ListScoresTool(scores, repertoire)

    assert tool.name == "list_scores"
    assert tool.arguments_model is ListScoresArguments
    result = await tool.execute(
        ListScoresArguments(work_reference=" NL15.2 ", choir="Lyon"), tool_context()
    )

    repertoire.search_titles.assert_awaited_once_with("Lyon", "NL15.2", reference=True)
    scores.list_scores.assert_awaited_once_with(work.id)
    assert result.structured == {"work_id": str(work.id), "scores": []}
    assert result.text == "This work has no scores."


@pytest.mark.anyio
async def test_ambiguous_title_does_not_read_scores() -> None:
    repertoire = create_autospec(RepertoireService, instance=True)
    scores = create_autospec(ScoreService, instance=True)
    now = FakeClock().now()
    choir_id = uuid4()
    matches = [
        Work(uuid4(), choir_id, WorkDetails("Peuple fidèle", composer), now, now)
        for composer in ("Composer A", "Composer B")
    ]
    repertoire.search_titles.return_value = matches

    result = await ListScoresTool(scores, repertoire).execute(
        ListScoresArguments(work_title="Peuple fidèle"), tool_context()
    )

    repertoire.search_titles.assert_awaited_once_with(None, "Peuple fidèle", reference=False)
    scores.list_scores.assert_not_awaited()
    assert result.structured == {
        "works": [
            {"id": str(match.id), "label": f"Peuple fidèle ({match.details.composer})"}
            for match in matches
        ],
        "work_count": 2,
    }
