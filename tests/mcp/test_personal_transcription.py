# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Exercise the personal-mode MCP workflow without displaying a view."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from dependency_injector import providers
from mcp.client import Client
from mcp.types import ImageContent, TextContent

from my_beautiful_choir.configuration.settings import Settings
from my_beautiful_choir.containers.application_container import ApplicationContainer
from my_beautiful_choir.containers.personal_mode_container import PersonalModeContainer
from my_beautiful_choir.repertoire.work import WorkDetails
from my_beautiful_choir.scores.pdf.pdf_page_renderer import PdfPageRenderer
from my_beautiful_choir.scores.recognition.errors import EngineNotFoundError
from my_beautiful_choir.scores.recognition.score_recognizer import ScoreRecognizer
from my_beautiful_choir.scores.score_origin import ScoreOrigin
from my_beautiful_choir.scores.sources.musicxml_score_source import MusicXmlScoreSource
from my_beautiful_choir.scores.sources.score_source import ScoreSource
from tests import score_samples
from tests.score_doubles import StubScoreSource


class _Recognizer(ScoreRecognizer):
    def __init__(self) -> None:
        self.calls = 0
        self.missing = False
        self.movement_count = 1

    @asynccontextmanager
    async def transcribe(self, pdf: bytes) -> AsyncIterator[tuple[ScoreSource, ...]]:
        assert pdf == score_samples.pdf()
        self.calls += 1
        if self.missing:
            raise EngineNotFoundError()
        yield tuple(
            StubScoreSource(score_samples.musicxml(), f"score-{number}.xml")
            for number in range(1, self.movement_count + 1)
        )


class _PageRenderer(PdfPageRenderer):
    async def render(self, pdf: bytes, page_number: int) -> tuple[bytes, int]:
        assert pdf == score_samples.pdf()
        assert page_number == 2
        return b"image", 2


async def _call(client: Client, name: str, **arguments: object) -> dict[str, Any]:
    result = await client.call_tool(name, dict(arguments))
    assert not result.is_error, result.content
    assert result.structured_content is not None
    return dict(result.structured_content)


async def _finish(client: Client, job: dict[str, Any]) -> dict[str, Any]:
    async with asyncio.timeout(5):
        while job["state"] == "pending":
            await asyncio.sleep(0.01)
            job = await _call(client, "get_transcription_status", job_id=job["job_id"])
    return job


@pytest.mark.anyio
async def test_local_transcription_and_musicxml_text_tools(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path)
    mode = PersonalModeContainer(settings=settings)
    container = ApplicationContainer(settings=settings, mode=mode)
    mode.views_directory.override(container.views_directory)
    recognizer = _Recognizer()
    mode.recognizer.override(providers.Object(recognizer))
    mode.pdf_page_renderer.override(providers.Object(_PageRenderer()))
    for step in mode.startup_steps():
        await step.run()
    await mode.choir_service().create("Choir")
    _, work = await mode.repertoire_service().add_work(None, WorkDetails(title="Song"))
    scores = mode.score_service()
    _, pdf = await scores.add_score(
        work.id, StubScoreSource(score_samples.pdf(), "Song.pdf"), "Source"
    )

    async with Client(container.server_builder().build(), raise_exceptions=False) as client:
        published = {tool.name: tool for tool in (await client.list_tools()).tools}
        assert published["transcribe_score"].meta is None
        found = await _call(client, "find_score_sources", work_title="Song", label="Sour")
        assert found["work_id"] == str(work.id)
        assert [item["id"] for item in found["scores"]] == [str(pdf.id)]
        failed = await client.call_tool(
            "add_musicxml_score", {"work_id": str(work.id), "xml": "<html/>"}
        )
        assert failed.is_error
        assert await scores.list_scores(work.id) == [pdf]

        job = await _finish(client, await _call(client, "transcribe_score", score_id=str(pdf.id)))
        assert job["state"] == "done", job
        xml_id = job["score"]["id"]
        assert job["scores"] == [job["score"]]
        same_job = await _call(client, "transcribe_score", score_id=str(pdf.id))
        assert same_job["score"]["id"] == xml_id
        assert recognizer.calls == 1
        chunk = await _call(client, "read_musicxml_score", score_id=xml_id, length=20)
        assert chunk["source_score_id"] == str(pdf.id)
        assert chunk["source_available"] is True
        assert chunk["xml"] == score_samples.musicxml_text()[:20]
        read = await client.call_tool(
            "read_musicxml_score", {"score_id": xml_id, "offset": chunk["next_offset"]}
        )
        assert isinstance(read.content[0], TextContent)
        assert read.content[0].text.endswith(score_samples.musicxml_text()[20:])
        page = await client.call_tool(
            "read_score_source_page", {"score_id": str(pdf.id), "page": 2}
        )
        assert isinstance(page.content[1], ImageContent)
        assert page.content[1].mime_type == "image/png"

        imported = await _call(
            client, "add_musicxml_score", work_id=str(work.id), xml=score_samples.musicxml_text()
        )
        added = await _call(client, "read_musicxml_score", score_id=imported["score"]["id"])
        assert added["xml"] == score_samples.musicxml_text()
        assert added["source_score_id"] is None
        assert added["source_available"] is None
        recognizer.missing = True
        failure = await _finish(
            client, await _call(client, "transcribe_score", score_id=str(pdf.id), recompute=True)
        )
        assert failure["state"] == "failed"
        assert failure["error_code"] == "engine_missing"
        assert failure["install_url"] == (
            "https://audiveris.github.io/audiveris/_pages/tutorials/install/binaries/"
        )
        assert len(await scores.list_scores(work.id)) == 3
        existing_source = MusicXmlScoreSource(
            score_samples.musicxml(), "Another result.musicxml", ScoreOrigin.TRANSCRIPTION
        )
        (existing,) = await scores.add_transcriptions(pdf.id, (existing_source,), reuse=True)
        assert str(existing.id) == xml_id
        assert len(await scores.list_scores(work.id)) == 3

        recognizer.missing = False
        recognizer.movement_count = 11
        multiple = await _finish(
            client, await _call(client, "transcribe_score", score_id=str(pdf.id), recompute=True)
        )
        assert multiple["state"] == "done"
        assert "score" not in multiple
        movement_ids = [item["id"] for item in multiple["scores"]]
        assert [item["movement_number"] for item in multiple["scores"]] == list(range(1, 12))
        repeated = await _call(client, "transcribe_score", score_id=str(pdf.id))
        assert repeated["scores"] == multiple["scores"]
        assert [str(item.id) for item in (await scores.list_scores(work.id))[-11:]] == movement_ids
        last = await _call(client, "read_musicxml_score", score_id=movement_ids[-1])
        assert last["source_score_id"] == str(pdf.id)
        assert last["xml"] == score_samples.musicxml_text()

        await scores.delete(await scores.describe_deletion(UUID(movement_ids[0])))
        retried = await _finish(
            client, await _call(client, "transcribe_score", score_id=str(pdf.id))
        )
        assert retried["state"] == "done"
        assert [item["movement_number"] for item in retried["scores"]] == list(range(1, 12))
        assert not set(movement_ids) & {item["id"] for item in retried["scores"]}
        retained = {str(item.id) for item in await scores.list_scores(work.id)}
        assert set(movement_ids[1:]) <= retained
        for item in retried["scores"]:
            await scores.delete(await scores.describe_deletion(UUID(item["id"])))
        assert await scores.latest_transcriptions(pdf.id) == ()

        await scores.delete(await scores.describe_deletion(pdf.id))
        unavailable = await client.call_tool("read_musicxml_score", {"score_id": xml_id})
        assert isinstance(unavailable.content[0], TextContent)
        assert "The source PDF is no longer available." in unavailable.content[0].text
        assert unavailable.structured_content is not None
        assert unavailable.structured_content["source_available"] is False
        assert unavailable.structured_content["source_score_id"] is None
        assert unavailable.structured_content["xml"] == score_samples.musicxml_text()
        _, stored = await scores.describe_score(existing.id)
        assert stored.source_score_id == pdf.id

    repertoire = mode.repertoire_service()
    await repertoire.delete(await repertoire.describe_deletion(work.id))
    async with mode.database().unit_of_work() as unit:
        assert await unit.transcription_runs.latest(pdf.id) is None
