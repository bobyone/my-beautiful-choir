# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of repertoire and work calls with in-memory services."""

from base64 import b64encode

import pytest
from pydantic import ValidationError

from my_beautiful_choir.authorization.errors import AccessDeniedError
from my_beautiful_choir.authorization.permission import Permission
from my_beautiful_choir.confirmation.memory.in_memory_pending_confirmations import (
    InMemoryPendingConfirmations,
)
from my_beautiful_choir.deletion.deletion_preview import DeletionPreview
from my_beautiful_choir.scores.errors import InvalidScoreError, UnsupportedScoreFormatError
from my_beautiful_choir.scores.sources.uploaded_score_source import UploadedScoreSource
from my_beautiful_choir.tools.view_tool.deletion.confirm_deletion_tool import (
    ConfirmDeletionArguments,
    ConfirmDeletionTool,
)
from my_beautiful_choir.tools.view_tool.repertoire.show_repertoire_tool import (
    ShowRepertoireArguments,
    ShowRepertoireTool,
)
from my_beautiful_choir.tools.view_tool.work.preview_deletion_from_work_view_tool import (
    PreviewDeletionFromWorkViewArguments,
    PreviewDeletionFromWorkViewTool,
)
from my_beautiful_choir.tools.view_tool.work.show_work_tool import ShowWorkArguments, ShowWorkTool
from my_beautiful_choir.tools.view_tool.work.upload_score_tool import (
    UploadScoreArguments,
    UploadScoreTool,
)
from tests import score_samples
from tests.doubles import DenyingAuthorization, StubView, tool_context
from tests.repertoire_world import RepertoireWorld

VIEW = StubView(uri="ui://my-beautiful-choir/work.html")


@pytest.mark.anyio
async def test_repertoire_reads_search_and_score_totals() -> None:
    world = RepertoireWorld()
    tool = ShowRepertoireTool(VIEW, world.repertoire(), world.choirs())
    empty = await tool.execute(ShowRepertoireArguments(), tool_context())
    assert empty.structured == {
        "choir": None,
        "choirs": [],
        "works": [],
        "search": "",
        "page": 1,
        "page_size": 10,
        "page_count": 1,
        "work_count": 0,
    }
    assert "first choir" in empty.text

    await world.choir("Lyon")
    await world.choir("Paris")
    work = await world.work("Lyon", "Étoile")
    await world.work("Lyon", "Other")
    other = await world.work("Paris", "Étoile")
    await world.score(work, "Alto")
    await world.score(other, "Soprano")
    result = await tool.execute(ShowRepertoireArguments(search="etoile"), tool_context())
    assert result.structured is not None
    assert result.structured["search"] == "etoile"
    assert result.structured["choir"] == "Lyon"
    assert result.structured["choirs"] == [
        {"name": "Lyon", "is_default": True},
        {"name": "Paris", "is_default": False},
    ]
    works = result.structured["works"]
    assert isinstance(works, list)
    [matched] = works
    assert matched["score_count"] == 1
    assert str(work.id) in result.text
    assert "1 work(s), page 1 of 1" in result.text


@pytest.mark.anyio
async def test_repertoire_pages() -> None:
    world = RepertoireWorld()
    tool = ShowRepertoireTool(VIEW, world.repertoire(), world.choirs())
    await world.choir("Lyon")
    for title in ["Delta", "Alpha", "Charlie", "Bravo", "Echo"]:
        await world.work("Lyon", title)
    result = await tool.execute(ShowRepertoireArguments(page=2, page_size=2), tool_context())
    data = result.structured
    assert data is not None
    works = data["works"]
    assert isinstance(works, list)
    assert [work["title"] for work in works] == ["Charlie", "Delta"]
    assert (data["page"], data["page_size"], data["page_count"], data["work_count"]) == (
        2,
        2,
        3,
        5,
    )
    assert "5 work(s), page 2 of 3" in result.text
    assert "Alpha" not in result.text
    with pytest.raises(ValidationError):
        ShowRepertoireArguments(page_size=101)
    with pytest.raises(ValidationError):
        ShowRepertoireArguments(page=0)


@pytest.mark.anyio
async def test_work_upload_and_deletion() -> None:
    world = RepertoireWorld()
    await world.choir("Lyon")
    work = await world.work("Lyon", "Étoile")
    scores = world.scores()
    show = ShowWorkTool(VIEW, world.repertoire(), scores)
    upload = UploadScoreTool(VIEW, scores, UploadedScoreSource)
    pending = InMemoryPendingConfirmations[DeletionPreview](world.clock)
    delete = PreviewDeletionFromWorkViewTool(VIEW, scores, pending)
    confirm = ConfirmDeletionTool(VIEW, [scores], pending)
    assert upload.app_only
    assert delete.app_only
    assert upload.view is VIEW
    assert upload.arguments_model is UploadScoreArguments
    assert delete.arguments_model is PreviewDeletionFromWorkViewArguments

    with pytest.raises(InvalidScoreError):
        await upload.execute(
            UploadScoreArguments(work_id=work.id, file_name="invalid.pdf", content="!!!!"),
            tool_context(),
        )
    with pytest.raises(UnsupportedScoreFormatError):
        await upload.execute(
            UploadScoreArguments(
                work_id=work.id, file_name="invalid.pdf", content="bm90IGEgc2NvcmU="
            ),
            tool_context(),
        )

    added = await upload.execute(
        UploadScoreArguments(
            work_id=work.id, file_name="Altos.pdf", content=b64encode(score_samples.pdf()).decode()
        ),
        tool_context(),
    )
    assert "Altos" in added.text
    shown = await show.execute(ShowWorkArguments(work_id=work.id), tool_context())
    assert "Altos" in shown.text
    assert shown.structured is not None
    assert shown.structured["choir"] == "Lyon"
    [score] = await scores.list_scores(work.id)
    assert score.label == "Altos"
    result = await delete.execute(
        PreviewDeletionFromWorkViewArguments(target_id=score.id), tool_context()
    )
    assert result.structured is not None
    assert result.structured["status"] == "pending"
    assert await scores.list_scores(work.id) == [score]
    confirmed = await confirm.execute(
        ConfirmDeletionArguments(token=str(result.structured["token"])), tool_context()
    )
    assert confirmed.structured is not None
    assert confirmed.structured["status"] == "deleted"
    assert await scores.list_scores(work.id) == []


@pytest.mark.anyio
async def test_views_preserve_service_authorization() -> None:
    world = RepertoireWorld()
    await world.choir("Lyon")
    work = await world.work("Lyon", "Étoile")
    denied = DenyingAuthorization(Permission.CONSULT_REPERTOIRE, Permission.MANAGE_REPERTOIRE)
    repertoire = ShowRepertoireTool(VIEW, world.repertoire(denied), world.choirs())
    with pytest.raises(AccessDeniedError):
        await repertoire.execute(ShowRepertoireArguments(), tool_context())
    delete = PreviewDeletionFromWorkViewTool(
        VIEW, world.repertoire(denied), InMemoryPendingConfirmations(world.clock)
    )
    with pytest.raises(AccessDeniedError):
        await delete.execute(
            PreviewDeletionFromWorkViewArguments(target_id=work.id), tool_context()
        )
    assert (await world.repertoire().get_work(work.id))[1] == work
