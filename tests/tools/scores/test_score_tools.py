# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the score tools, with the services on in-memory doubles."""

from pathlib import Path
from uuid import uuid4

import pytest

from my_beautiful_choir.authorization.local.local_user_authorization import LocalUserAuthorization
from my_beautiful_choir.choirs.choir_service import ChoirService
from my_beautiful_choir.repertoire.repertoire_service import RepertoireService
from my_beautiful_choir.repertoire.work import Work, WorkDetails
from my_beautiful_choir.scores.errors import ScoreNotFoundError
from my_beautiful_choir.scores.formats.score_format_detector import ScoreFormatDetector
from my_beautiful_choir.scores.formats.signatures.pdf_signature import PdfSignature
from my_beautiful_choir.scores.musicxml.musicxml_score_validator import MusicXmlScoreValidator
from my_beautiful_choir.scores.score_origin import ScoreOrigin
from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.scores.sources.errors import UnsupportedLinkError
from my_beautiful_choir.scores.sources.google_drive.google_drive_link import GoogleDriveLink
from my_beautiful_choir.scores.sources.score_source import ScoreSource
from my_beautiful_choir.tools.scores.add_score_from_file_tool import (
    AddScoreFromFileArguments,
    AddScoreFromFileTool,
)
from my_beautiful_choir.tools.scores.add_score_from_google_drive_tool import (
    AddScoreFromGoogleDriveArguments,
    AddScoreFromGoogleDriveTool,
)
from my_beautiful_choir.tools.scores.get_score_file_tool import (
    GetScoreFileArguments,
    GetScoreFileTool,
)
from my_beautiful_choir.tools.scores.open_score_tool import OpenScoreArguments, OpenScoreTool
from my_beautiful_choir.tools.tool_file import ToolFile
from tests import score_samples
from tests.doubles import FakeClock, tool_context
from tests.persistence_doubles import InMemoryDatabase
from tests.score_doubles import InMemoryFileStorage, SpyScoreOpener, StubScoreSource

FILE_ID = "1aBcD_eFgH-ijKlMnOpQrStUvWxYz0123"


class _Fixture:
    def __init__(self) -> None:
        self.database = InMemoryDatabase()
        self.clock = FakeClock()
        self.opener = SpyScoreOpener()
        self.links: list[GoogleDriveLink] = []
        self.storage = InMemoryFileStorage()
        self.service = ScoreService(
            self.database.unit_of_work,
            self.clock,
            LocalUserAuthorization(),
            self.storage,
            ScoreFormatDetector([PdfSignature()]),
            self.opener,
            validator=MusicXmlScoreValidator(),
        )

    def google_drive_source(self, link: GoogleDriveLink) -> ScoreSource:
        self.links.append(link)
        return StubScoreSource(
            score_samples.pdf(), "Requiem.pdf", ScoreOrigin.GOOGLE_DRIVE, link.url
        )

    async def work(self) -> Work:
        authorization = LocalUserAuthorization()
        await ChoirService(
            self.database.unit_of_work, self.clock, authorization, InMemoryFileStorage()
        ).create("Chœur")
        repertoire = RepertoireService(
            self.database.unit_of_work, self.clock, authorization, InMemoryFileStorage()
        )
        _, work = await repertoire.add_work(None, WorkDetails(title="Ave Maria", composer="Bach"))
        return work


@pytest.fixture
def fixture() -> _Fixture:
    return _Fixture()


@pytest.mark.anyio
async def test_add_from_a_file_then_open(fixture: _Fixture, tmp_path: Path) -> None:
    work = await fixture.work()
    path = tmp_path / "Ave Maria.pdf"
    path.write_bytes(score_samples.pdf())
    tool = AddScoreFromFileTool(fixture.service)
    assert tool.name == "add_score_from_file"
    assert "absolute path" in tool.description
    assert tool.arguments_model is AddScoreFromFileArguments
    added = await tool.execute(
        AddScoreFromFileArguments(work_id=work.id, path=str(path)), tool_context()
    )
    score = added.structured["score"]
    assert isinstance(score, dict)
    assert added.text == (
        f"The score 'Ave Maria' (final v1) (PDF) was added to the work Ave Maria (Bach); "
        f"its id is {score['id']}."
    )
    assert added.structured["work_id"] == str(work.id)
    assert score["origin"] == "local_file"
    assert score["format"] == "pdf"
    assert score["original_name"] == "Ave Maria.pdf"
    assert score["link"] is None
    assert score["added_at"] == "2026-11-21T12:00:00+00:00"

    open_tool = OpenScoreTool(fixture.service)
    assert open_tool.name == "open_score"
    assert open_tool.arguments_model is OpenScoreArguments
    assert "copy" in open_tool.description
    opened = await open_tool.execute(OpenScoreArguments(score_id=score["id"]), tool_context())
    assert opened.text == (
        "The score 'Ave Maria' (final v1) of the work Ave Maria (Bach) "
        "was opened on the user's computer."
    )
    assert opened.structured["score"] == score
    assert len(fixture.opener.opened) == 1


@pytest.mark.anyio
async def test_add_from_google_drive(fixture: _Fixture) -> None:
    work = await fixture.work()
    tool = AddScoreFromGoogleDriveTool(fixture.service, fixture.google_drive_source)
    assert tool.name == "add_score_from_google_drive"
    assert "Folder links" in tool.description
    assert tool.arguments_model is AddScoreFromGoogleDriveArguments
    link = f"https://drive.google.com/file/d/{FILE_ID}/view?usp=sharing"
    added = await tool.execute(
        AddScoreFromGoogleDriveArguments(work_id=work.id, link=link, label="Full score"),
        tool_context(),
    )
    assert fixture.links == [GoogleDriveLink(FILE_ID)]
    score = added.structured["score"]
    assert isinstance(score, dict)
    assert score["label"] == "Full score"
    assert score["origin"] == "google_drive"
    assert score["link"] == f"https://drive.google.com/file/d/{FILE_ID}/view"


@pytest.mark.anyio
async def test_an_unsupported_link_downloads_nothing(fixture: _Fixture) -> None:
    work = await fixture.work()
    tool = AddScoreFromGoogleDriveTool(fixture.service, fixture.google_drive_source)
    with pytest.raises(UnsupportedLinkError):
        await tool.execute(
            AddScoreFromGoogleDriveArguments(
                work_id=work.id, link=f"https://drive.google.com/drive/folders/{FILE_ID}"
            ),
            tool_context(),
        )
    assert fixture.links == []


@pytest.mark.anyio
async def test_open_a_missing_score(fixture: _Fixture) -> None:
    with pytest.raises(ScoreNotFoundError):
        await OpenScoreTool(fixture.service).execute(
            OpenScoreArguments(score_id=uuid4()), tool_context()
        )


@pytest.mark.anyio
async def test_get_score_file_gives_back_the_stored_file(fixture: _Fixture) -> None:
    work = await fixture.work()
    _, score = await fixture.service.add_score(
        work.id, StubScoreSource(score_samples.pdf(), "Ave Maria é alto.pdf"), "Alto"
    )
    tool = GetScoreFileTool(fixture.service)
    assert tool.name == "get_score_file"
    assert tool.view is None
    assert not tool.app_only
    result = await tool.execute(GetScoreFileArguments(score_id=score.id), tool_context())
    assert result.files == (
        ToolFile("Ave Maria é alto.pdf", "application/pdf", score_samples.pdf()),
    )
    assert "'Alto'" in result.text
    assert "'Ave Maria é alto.pdf'" in result.text
    assert result.structured["work_id"] == str(work.id)
    assert fixture.opener.opened == []


@pytest.mark.anyio
async def test_get_score_file_gives_back_a_score_above_2_megabytes(fixture: _Fixture) -> None:
    work = await fixture.work()
    content = score_samples.pdf() + b"0" * (2 * 1024 * 1024)
    _, score = await fixture.service.add_score(work.id, StubScoreSource(content, "Full.pdf"))
    result = await GetScoreFileTool(fixture.service).execute(
        GetScoreFileArguments(score_id=score.id), tool_context()
    )
    assert result.files == (ToolFile("Full.pdf", "application/pdf", content),)


@pytest.mark.anyio
async def test_get_a_missing_score_file(fixture: _Fixture) -> None:
    with pytest.raises(ScoreNotFoundError):
        await GetScoreFileTool(fixture.service).execute(
            GetScoreFileArguments(score_id=uuid4()), tool_context()
        )


@pytest.mark.anyio
async def test_get_score_file_names_the_file_with_the_extension_of_its_format(
    fixture: _Fixture,
) -> None:
    work = await fixture.work()
    _, score = await fixture.service.add_score(
        work.id, StubScoreSource(score_samples.pdf(), "Requiem.mscz"), "Requiem"
    )
    result = await GetScoreFileTool(fixture.service).execute(
        GetScoreFileArguments(score_id=score.id), tool_context()
    )
    [file] = result.files
    assert file.name == "Requiem.pdf"
    assert result.structured["score"]["original_name"] == "Requiem.mscz"  # type: ignore[index]
