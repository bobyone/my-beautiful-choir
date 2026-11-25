# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the score service, with in-memory doubles."""

from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from my_beautiful_choir.authorization.authorization import Authorization
from my_beautiful_choir.authorization.errors import AccessDeniedError
from my_beautiful_choir.authorization.local.local_user_authorization import LocalUserAuthorization
from my_beautiful_choir.authorization.permission import Permission
from my_beautiful_choir.choirs.choir_service import ChoirService
from my_beautiful_choir.repertoire.errors import WorkNotFoundError
from my_beautiful_choir.repertoire.repertoire_service import RepertoireService
from my_beautiful_choir.repertoire.work import Work, WorkDetails
from my_beautiful_choir.scores.errors import (
    DraftScoreNotAllowedError,
    FinalScoreProtectedError,
    InvalidScoreError,
    InvalidScoreSizeError,
    ScoreFileMissingError,
    ScoreNotDuplicableError,
    ScoreNotFoundError,
    ScoreOpenError,
    StaleFinalisationError,
    StoredScoreTooLargeError,
    UnsupportedScoreFormatError,
)
from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.formats.score_format_detector import ScoreFormatDetector
from my_beautiful_choir.scores.formats.signatures.music_xml_signature import MusicXmlSignature
from my_beautiful_choir.scores.formats.signatures.pdf_signature import PdfSignature
from my_beautiful_choir.scores.formats.signatures.zip.compressed_music_xml_signature import (
    CompressedMusicXmlSignature,
)
from my_beautiful_choir.scores.formats.signatures.zip.muse_score_signature import (
    MuseScoreSignature,
)
from my_beautiful_choir.scores.musicxml.musicxml_score_validator import MusicXmlScoreValidator
from my_beautiful_choir.scores.score import Score
from my_beautiful_choir.scores.score_origin import ScoreOrigin
from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.scores.score_state import ScoreState
from my_beautiful_choir.scores.sources.errors import UnreadableLocalFileError
from my_beautiful_choir.scores.sources.score_content import ScoreContent
from my_beautiful_choir.storage.errors import StorageError
from tests import score_samples
from tests.doubles import DenyingAuthorization, FakeClock
from tests.persistence_doubles import InMemoryDatabase, InMemoryScoreRepository
from tests.score_doubles import InMemoryFileStorage, SpyScoreOpener, StubScoreSource

LIMIT = 4096


class _Fixture:
    def __init__(self) -> None:
        self.database = InMemoryDatabase()
        self.clock = FakeClock()
        self.storage = InMemoryFileStorage()
        self.opener = SpyScoreOpener()
        self.detector = ScoreFormatDetector(
            [
                PdfSignature(),
                MuseScoreSignature(),
                CompressedMusicXmlSignature(),
                MusicXmlSignature(),
            ]
        )

    def service(self, authorization: Authorization | None = None) -> ScoreService:
        return self.service_with_maximum(LIMIT, authorization)

    def service_with_maximum(
        self, maximum_size: int, authorization: Authorization | None = None
    ) -> ScoreService:
        return ScoreService(
            self.database.unit_of_work,
            self.clock,
            authorization or LocalUserAuthorization(),
            self.storage,
            self.detector,
            self.opener,
            maximum_size=maximum_size,
            validator=MusicXmlScoreValidator(),
        )

    async def work(self) -> Work:
        authorization = LocalUserAuthorization()
        await ChoirService(
            self.database.unit_of_work, self.clock, authorization, InMemoryFileStorage()
        ).create("Chœur")
        repertoire = RepertoireService(
            self.database.unit_of_work, self.clock, authorization, InMemoryFileStorage()
        )
        _, work = await repertoire.add_work(None, WorkDetails(title="Ave Maria"))
        return work


@pytest.fixture
def fixture() -> _Fixture:
    return _Fixture()


@pytest.mark.anyio
async def test_duplicate_and_finalise_a_score(fixture: _Fixture) -> None:
    work = await fixture.work()
    service = fixture.service()
    _, source = await service.add_score(work.id, StubScoreSource(score_samples.musicxml()))
    assert source.state is ScoreState.FINAL
    assert source.version_number == 1
    with pytest.raises(FinalScoreProtectedError):
        await service.describe_draft_for_editing(source.id)
    _, draft = await service.duplicate_as_draft(source.id)
    assert draft.state is ScoreState.DRAFT
    assert draft.storage_key != source.storage_key
    assert draft.originating_score is not None
    assert draft.originating_score.id == source.id
    assert draft.originating_score.version_number == 1
    with pytest.raises(DraftScoreNotAllowedError):
        await service.read_final_score(draft.id)
    await service.delete(await service.describe_deletion(source.id))
    report, preview = await service.preview_finalisation(draft.id)
    assert not report.errors
    assert preview is not None
    _, final = await service.finalise(preview)
    assert final.id == draft.id
    assert final.originating_score == draft.originating_score
    assert final.version_number == 2
    assert (await service.read_final_score(final.id))[2] == score_samples.musicxml()
    with pytest.raises(StaleFinalisationError):
        await service.finalise(preview)


@pytest.mark.anyio
async def test_can_duplicate_a_compressed_score_but_requires_permission_to_finalise(
    fixture: _Fixture,
) -> None:
    work = await fixture.work()
    service = fixture.service()
    content = score_samples.compressed_musicxml()
    _, original = await service.add_score(work.id, StubScoreSource(content, "Score.mxl"))
    _, draft = await service.duplicate_as_draft(original.id)
    assert draft.format is ScoreFormat.COMPRESSED_MUSICXML
    assert fixture.storage.files[draft.storage_key] == content
    _, preview = await service.preview_finalisation(draft.id)
    assert preview is not None
    denied = fixture.service(DenyingAuthorization(Permission.MANAGE_REPERTOIRE))
    with pytest.raises(AccessDeniedError):
        await denied.finalise(preview)
    assert (await service.describe_score(draft.id))[1].state is ScoreState.DRAFT


@pytest.mark.anyio
async def test_preview_rejects_invalid_and_stale_content(fixture: _Fixture) -> None:
    work = await fixture.work()
    service = fixture.service()
    _, draft = await service.add_score(
        work.id, StubScoreSource(score_samples.musicxml(), origin=ScoreOrigin.MUSICXML_TEXT)
    )
    assert draft.state is ScoreState.DRAFT
    _, preview = await service.preview_finalisation(draft.id)
    assert preview is not None
    fixture.storage.files[draft.storage_key] = b"<score-partwise>"
    with pytest.raises(StaleFinalisationError):
        await service.finalise(preview)
    report, new_preview = await service.preview_finalisation(draft.id)
    assert report.errors
    assert new_preview is None
    _, pdf = await service.add_score(work.id, StubScoreSource(score_samples.pdf()))
    with pytest.raises(ScoreNotDuplicableError):
        await service.duplicate_as_draft(pdf.id)


@pytest.mark.anyio
async def test_add_stores_the_content_and_saves_the_score(fixture: _Fixture) -> None:
    work = await fixture.work()
    source = StubScoreSource(score_samples.pdf(), "Ave Maria (SATB).pdf")
    added_work, score = await fixture.service().add_score(work.id, source)
    assert added_work == work
    assert source.limits == [LIMIT]
    assert score.work_id == work.id
    assert score.label == "Ave Maria (SATB)"
    assert score.format is ScoreFormat.PDF
    assert score.size == len(score_samples.pdf())
    assert score.original_name == "Ave Maria (SATB).pdf"
    assert score.origin is ScoreOrigin.FILE_PICKER
    assert score.link is None
    assert score.added_at == fixture.clock.start
    assert score.storage_key == f"choirs/{work.choir_id}/scores/{score.id}"
    assert fixture.storage.files == {score.storage_key: score_samples.pdf()}
    assert await fixture.service().list_scores(work.id) == [score]


@pytest.mark.anyio
async def test_transcription_movements_share_the_publication_time(
    fixture: _Fixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    work = await fixture.work()
    service = fixture.service()
    source = StubScoreSource(score_samples.pdf())
    _, pdf = await service.add_score(work.id, source)
    store = fixture.storage.store
    concurrent_scores: list[Score] = []

    async def store_with_concurrent_upload(key: str, content: bytes) -> None:
        await store(key, content)
        if content == score_samples.musicxml() and not concurrent_scores:
            fixture.clock.advance(timedelta(seconds=1))
            _, score = await service.add_score(work.id, source, "Other PDF")
            concurrent_scores.append(score)
            fixture.clock.advance(timedelta(seconds=1))

    monkeypatch.setattr(fixture.storage, "store", store_with_concurrent_upload)
    movement = StubScoreSource(score_samples.musicxml())
    first, second = await service.add_transcriptions(pdf.id, (movement, movement), reuse=False)

    assert first.added_at == second.added_at == fixture.clock.now()
    assert await service.list_scores(work.id) == [pdf, *concurrent_scores, first, second]


@pytest.mark.anyio
async def test_transcription_storage_failure_discards_all_staged_scores(
    fixture: _Fixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    work = await fixture.work()
    service = fixture.service()
    _, pdf = await service.add_score(work.id, StubScoreSource(score_samples.pdf()))
    store = fixture.storage.store

    async def fail_on_second_movement(key: str, content: bytes) -> None:
        if len(fixture.storage.files) == 2:
            raise StorageError(key, "disk full")
        await store(key, content)

    monkeypatch.setattr(fixture.storage, "store", fail_on_second_movement)
    movement = StubScoreSource(score_samples.musicxml())
    with pytest.raises(StorageError, match="disk full"):
        await service.add_transcriptions(pdf.id, (movement, movement), reuse=False)
    assert await service.list_scores(work.id) == [pdf]
    assert fixture.storage.files == {pdf.storage_key: score_samples.pdf()}
    assert fixture.database.data.runs == []


@pytest.mark.anyio
async def test_transcription_database_failure_rolls_back_run_and_scores(
    fixture: _Fixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    work = await fixture.work()
    service = fixture.service()
    _, pdf = await service.add_score(work.id, StubScoreSource(score_samples.pdf()))
    original_add = InMemoryScoreRepository.add

    async def fail_on_second_movement(repository: InMemoryScoreRepository, score: Score) -> None:
        if score.movement_number == 2:
            raise RuntimeError("Database write failed.")
        await original_add(repository, score)

    monkeypatch.setattr(InMemoryScoreRepository, "add", fail_on_second_movement)
    movement = StubScoreSource(score_samples.musicxml())
    with pytest.raises(RuntimeError, match="Database write failed"):
        await service.add_transcriptions(pdf.id, (movement, movement), reuse=False)
    assert await service.list_scores(work.id) == [pdf]
    assert fixture.storage.files == {pdf.storage_key: score_samples.pdf()}
    assert fixture.database.data.runs == []


@pytest.mark.anyio
async def test_add_keeps_the_label_origin_and_link(fixture: _Fixture) -> None:
    work = await fixture.work()
    source = StubScoreSource(
        score_samples.musescore(),
        "Google Drive file",
        ScoreOrigin.GOOGLE_DRIVE,
        "https://drive.google.com/file/d/abcdefghijkl/view",
    )
    _, score = await fixture.service().add_score(work.id, source, " Alto part ")
    assert score.label == "Alto part"
    assert score.format is ScoreFormat.MUSESCORE
    assert score.origin is ScoreOrigin.GOOGLE_DRIVE
    assert score.link == "https://drive.google.com/file/d/abcdefghijkl/view"


@pytest.mark.anyio
async def test_the_same_file_may_be_added_twice(fixture: _Fixture) -> None:
    work = await fixture.work()
    service = fixture.service()
    _, first = await service.add_score(work.id, StubScoreSource(score_samples.pdf()), "Soprano")
    fixture.clock.advance(timedelta(minutes=1))
    _, second = await service.add_score(work.id, StubScoreSource(score_samples.pdf()), "Alto")
    assert first.storage_key != second.storage_key
    assert [score.label for score in await service.list_scores(work.id)] == ["Soprano", "Alto"]


@pytest.mark.anyio
async def test_add_to_a_missing_work(fixture: _Fixture) -> None:
    source = StubScoreSource(score_samples.pdf())
    with pytest.raises(WorkNotFoundError):
        await fixture.service().add_score(uuid4(), source)
    assert source.limits == []


@pytest.mark.anyio
@pytest.mark.parametrize("content", [b"", b"x" * (LIMIT + 1)])
async def test_add_an_empty_or_too_large_content(fixture: _Fixture, content: bytes) -> None:
    work = await fixture.work()
    with pytest.raises(InvalidScoreSizeError) as raised:
        await fixture.service().add_score(work.id, StubScoreSource(content))
    assert raised.value.limit == LIMIT
    assert fixture.storage.files == {}


@pytest.mark.anyio
async def test_add_a_content_that_is_not_a_score(fixture: _Fixture) -> None:
    work = await fixture.work()
    with pytest.raises(UnsupportedScoreFormatError):
        await fixture.service().add_score(work.id, StubScoreSource(b"secret key"))
    assert fixture.storage.files == {}
    assert fixture.database.data.scores == {}


@pytest.mark.anyio
async def test_add_with_a_label_too_long(fixture: _Fixture) -> None:
    work = await fixture.work()
    with pytest.raises(InvalidScoreError):
        await fixture.service().add_score(work.id, StubScoreSource(score_samples.pdf()), "a" * 101)
    assert fixture.storage.files == {}


@pytest.mark.anyio
async def test_a_source_error_reaches_the_caller(fixture: _Fixture) -> None:
    work = await fixture.work()

    class _Unreadable(StubScoreSource):
        async def fetch(self, limit: int) -> ScoreContent:
            raise UnreadableLocalFileError(Path("/missing.pdf"), "missing")

    with pytest.raises(UnreadableLocalFileError):
        await fixture.service().add_score(work.id, _Unreadable(b""))


@pytest.mark.anyio
async def test_a_storage_failure_saves_nothing(fixture: _Fixture) -> None:
    work = await fixture.work()
    fixture.storage.failing = True
    with pytest.raises(StorageError):
        await fixture.service().add_score(work.id, StubScoreSource(score_samples.pdf()))
    assert fixture.database.data.scores == {}


@pytest.mark.anyio
async def test_the_content_is_removed_when_the_work_disappeared_meanwhile(
    fixture: _Fixture,
) -> None:
    work = await fixture.work()
    database = fixture.database

    class _DeletingSource(StubScoreSource):
        async def fetch(self, limit: int) -> ScoreContent:
            async with database.unit_of_work() as unit_of_work:
                await unit_of_work.works.delete(work.id)
                await unit_of_work.commit()
            return await super().fetch(limit)

    with pytest.raises(WorkNotFoundError):
        await fixture.service().add_score(work.id, _DeletingSource(score_samples.pdf()))
    assert fixture.storage.files == {}


@pytest.mark.anyio
async def test_a_content_left_after_a_failed_removal_is_logged(
    fixture: _Fixture, caplog: pytest.LogCaptureFixture
) -> None:
    work = await fixture.work()
    database = fixture.database
    storage = fixture.storage

    async def fail_delete(key: str) -> None:
        raise StorageError(key, "locked")

    class _DeletingSource(StubScoreSource):
        async def fetch(self, limit: int) -> ScoreContent:
            async with database.unit_of_work() as unit_of_work:
                await unit_of_work.works.delete(work.id)
                await unit_of_work.commit()
            storage.delete = fail_delete  # type: ignore[method-assign]
            return await super().fetch(limit)

    with pytest.raises(WorkNotFoundError):
        await fixture.service().add_score(work.id, _DeletingSource(score_samples.pdf()))
    assert "A stored content could not be deleted and is left" in caplog.text


@pytest.mark.anyio
async def test_add_requires_the_right_to_manage_the_repertoire(fixture: _Fixture) -> None:
    work = await fixture.work()
    service = fixture.service(DenyingAuthorization(Permission.MANAGE_REPERTOIRE))
    source = StubScoreSource(score_samples.pdf())
    with pytest.raises(AccessDeniedError):
        await service.add_score(work.id, source)
    assert source.limits == []


@pytest.mark.anyio
async def test_list_scores_of_a_missing_work_or_without_right(fixture: _Fixture) -> None:
    with pytest.raises(WorkNotFoundError):
        await fixture.service().list_scores(uuid4())
    work = await fixture.work()
    denied = fixture.service(DenyingAuthorization(Permission.CONSULT_REPERTOIRE))
    with pytest.raises(AccessDeniedError):
        await denied.list_scores(work.id)


@pytest.mark.anyio
async def test_read_gives_the_stored_content_without_changing_anything(fixture: _Fixture) -> None:
    work = await fixture.work()
    service = fixture.service()
    _, score = await service.add_score(work.id, StubScoreSource(score_samples.pdf()), "Alto")
    stored = dict(fixture.storage.files)
    assert await service.read_score(score.id) == (work, score, score_samples.pdf())
    assert fixture.storage.files == stored
    assert await service.list_scores(work.id) == [score]
    assert fixture.opener.opened == []


@pytest.mark.anyio
async def test_read_a_missing_score_or_a_missing_file(fixture: _Fixture) -> None:
    service = fixture.service()
    with pytest.raises(ScoreNotFoundError):
        await service.read_score(uuid4())
    work = await fixture.work()
    _, score = await service.add_score(work.id, StubScoreSource(score_samples.pdf()), "Alto")
    fixture.storage.files.clear()
    with pytest.raises(ScoreFileMissingError):
        await service.read_score(score.id)


@pytest.mark.anyio
async def test_read_accepts_a_score_of_exactly_the_maximum(fixture: _Fixture) -> None:
    work = await fixture.work()
    service = fixture.service()
    content = score_samples.pdf().ljust(LIMIT, b"0")
    _, score = await service.add_score(work.id, StubScoreSource(content))
    _, _, read = await service.read_score(score.id)
    assert read == content
    assert fixture.storage.reads == [(score.storage_key, LIMIT)]


@pytest.mark.anyio
async def test_read_refuses_a_stored_file_above_the_maximum_despite_its_record(
    fixture: _Fixture,
) -> None:
    work = await fixture.work()
    service = fixture.service()
    _, score = await service.add_score(work.id, StubScoreSource(score_samples.pdf()), "Alto")
    fixture.storage.files[score.storage_key] = score_samples.pdf().ljust(LIMIT + 1000, b"0")
    with pytest.raises(StoredScoreTooLargeError) as raised:
        await service.read_score(score.id)
    assert (raised.value.label, raised.value.limit) == ("Alto", LIMIT)
    assert fixture.storage.reads == [(score.storage_key, LIMIT)]


@pytest.mark.anyio
async def test_read_refuses_a_recorded_size_above_the_maximum_before_reading(
    fixture: _Fixture,
) -> None:
    work = await fixture.work()
    _, score = await fixture.service().add_score(work.id, StubScoreSource(score_samples.pdf()))
    smaller = fixture.service_with_maximum(score.size - 1)
    with pytest.raises(StoredScoreTooLargeError):
        await smaller.read_score(score.id)
    assert fixture.storage.reads == []


@pytest.mark.anyio
async def test_read_requires_the_right_to_consult_the_repertoire(fixture: _Fixture) -> None:
    work = await fixture.work()
    _, score = await fixture.service().add_score(work.id, StubScoreSource(score_samples.pdf()))
    denied = fixture.service(DenyingAuthorization(Permission.CONSULT_REPERTOIRE))
    with pytest.raises(AccessDeniedError):
        await denied.read_score(score.id)


@pytest.mark.anyio
async def test_open_gives_the_stored_content_to_the_opener(fixture: _Fixture) -> None:
    work = await fixture.work()
    service = fixture.service()
    _, score = await service.add_score(work.id, StubScoreSource(score_samples.pdf()))
    opened_work, opened = await service.open_score(score.id)
    assert (opened_work, opened) == (work, score)
    assert fixture.opener.opened == [(score, score_samples.pdf())]


@pytest.mark.anyio
async def test_open_a_missing_score(fixture: _Fixture) -> None:
    with pytest.raises(ScoreNotFoundError):
        await fixture.service().open_score(uuid4())


@pytest.mark.anyio
async def test_open_a_score_whose_file_is_missing(fixture: _Fixture) -> None:
    work = await fixture.work()
    service = fixture.service()
    _, score = await service.add_score(work.id, StubScoreSource(score_samples.pdf()), "Alto")
    fixture.storage.files.clear()
    with pytest.raises(ScoreFileMissingError) as raised:
        await service.open_score(score.id)
    assert "'Alto'" in str(raised.value)
    assert fixture.opener.opened == []


@pytest.mark.anyio
async def test_an_opening_failure_reaches_the_caller(fixture: _Fixture) -> None:
    work = await fixture.work()
    service = fixture.service()
    _, score = await service.add_score(work.id, StubScoreSource(score_samples.pdf()))
    fixture.opener.error = ScoreOpenError(ScoreFormat.PDF, "no application")
    with pytest.raises(ScoreOpenError) as raised:
        await service.open_score(score.id)
    assert "PDF files (.pdf)" in str(raised.value)


@pytest.mark.anyio
async def test_open_requires_the_right_to_consult_the_repertoire(fixture: _Fixture) -> None:
    work = await fixture.work()
    _, score = await fixture.service().add_score(work.id, StubScoreSource(score_samples.pdf()))
    denied = fixture.service(DenyingAuthorization(Permission.CONSULT_REPERTOIRE))
    with pytest.raises(AccessDeniedError):
        await denied.open_score(score.id)
    assert fixture.opener.opened == []
