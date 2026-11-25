# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Verify finalisation through the server's MCP Apps boundary."""

from contextlib import nullcontext
from pathlib import Path

import pytest
from mcp.client import Client
from mcp.server.mcpserver import MCPServer

from my_beautiful_choir.configuration.score_lifecycle_settings import ScoreLifecycleSettings
from my_beautiful_choir.configuration.settings import Settings
from my_beautiful_choir.containers.application_container import ApplicationContainer
from my_beautiful_choir.containers.personal_mode_container import PersonalModeContainer
from my_beautiful_choir.mcp.connection_scope import stdio_connection_scope
from my_beautiful_choir.repertoire.work import WorkDetails
from my_beautiful_choir.scores.score import Score
from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.scores.score_state import ScoreState
from tests import score_samples
from tests.score_doubles import StubScoreSource


async def _server_with_draft(settings: Settings) -> tuple[MCPServer, ScoreService, Score]:
    mode = PersonalModeContainer(settings=settings)
    container = ApplicationContainer(settings=settings, mode=mode)
    mode.views_directory.override(container.views_directory)
    for step in mode.startup_steps():
        await step.run()
    await mode.choir_service().create("Choir")
    _, work = await mode.repertoire_service().add_work(None, WorkDetails(title="Song"))
    service = mode.score_service()
    _, source = await service.add_score(work.id, StubScoreSource(score_samples.musicxml()))
    _, draft = await service.duplicate_as_draft(source.id)
    return container.server_builder().build(), service, draft


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("lifecycle", "connected"),
    [
        pytest.param(ScoreLifecycleSettings(), True, id="disabled-by-default"),
        pytest.param(
            ScoreLifecycleSettings(trusted_finalisation_host=True), False, id="no-session"
        ),
    ],
)
async def test_preview_withholds_token_when_finalisation_is_unavailable(
    tmp_path: Path, lifecycle: ScoreLifecycleSettings, connected: bool
) -> None:
    settings = Settings(data_dir=tmp_path, score_lifecycle=lifecycle)
    server, service, draft = await _server_with_draft(settings)
    with stdio_connection_scope() if connected else nullcontext():
        async with Client(server, raise_exceptions=False) as client:
            preview = await client.call_tool(
                "preview_score_finalisation", {"score_id": str(draft.id)}
            )

    assert not preview.is_error
    assert "finalisation_token" not in (preview.meta or {})
    assert "finalisation" not in (preview.structured_content or {})
    assert draft.state is ScoreState.DRAFT
    assert (await service.describe_score(draft.id))[1] == draft


@pytest.mark.anyio
async def test_confirmation_uses_private_session_bound_single_use_token(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path, score_lifecycle=ScoreLifecycleSettings(trusted_finalisation_host=True)
    )
    server, service, draft = await _server_with_draft(settings)
    with stdio_connection_scope():
        await _verify_confirmation(Client(server, raise_exceptions=False), service, draft)


async def _verify_confirmation(client: Client, service: ScoreService, draft: Score) -> None:
    async with client:
        published = {tool.name: tool for tool in (await client.list_tools()).tools}
        meta = published["confirm_score_finalisation"].meta
        assert meta is not None
        assert meta["ui"]["visibility"] == ["app"]
        arguments = {"score_id": str(draft.id)}
        refusal = await client.call_tool("confirm_score_finalisation", {"token": "unknown"})
        assert refusal.structured_content == {"finalisation_stale": True}
        preview = await client.call_tool("preview_score_finalisation", arguments)
        assert not preview.is_error
        assert preview.meta is not None
        token = preview.meta["finalisation_token"]
        assert token not in str(preview.content)
        assert token not in str(preview.structured_content)
        assert (await service.describe_score(draft.id))[1].state is ScoreState.DRAFT
        final = await client.call_tool("confirm_score_finalisation", {"token": token})
        assert not final.is_error
        assert final.structured_content is not None
        assert final.structured_content["score"]["state"] == "final"
        assert final.structured_content["score"]["version_number"] == 2
        replay = await client.call_tool("confirm_score_finalisation", {"token": token})
        assert replay.structured_content == {"finalisation_stale": True}
