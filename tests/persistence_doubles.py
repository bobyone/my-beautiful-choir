# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""In-memory doubles of the unit of work and the repositories."""

import builtins
import copy
from collections.abc import Collection
from dataclasses import dataclass, field, replace
from types import TracebackType
from typing import Self
from uuid import UUID

from my_beautiful_choir.choirs.choir import Choir
from my_beautiful_choir.choirs.choir_name import choir_name_key
from my_beautiful_choir.choirs.choir_repository import ChoirRepository
from my_beautiful_choir.choirs.errors import ChoirNotFoundError
from my_beautiful_choir.persistence.unit_of_work import UnitOfWork
from my_beautiful_choir.repertoire.errors import WorkNotFoundError
from my_beautiful_choir.repertoire.work import Work
from my_beautiful_choir.repertoire.work_repository import WorkRepository
from my_beautiful_choir.repertoire.work_rules import search_text
from my_beautiful_choir.scores.errors import ScoreNotFoundError
from my_beautiful_choir.scores.recognition.transcription_run import TranscriptionRun
from my_beautiful_choir.scores.recognition.transcription_run_repository import (
    TranscriptionRunRepository,
)
from my_beautiful_choir.scores.score import Score
from my_beautiful_choir.scores.score_repository import ScoreRepository


@dataclass
class InMemoryData:
    """Content of the in-memory data store."""

    choirs: dict[UUID, Choir] = field(default_factory=dict)
    works: dict[UUID, Work] = field(default_factory=dict)
    scores: dict[UUID, Score] = field(default_factory=dict)
    runs: list[TranscriptionRun] = field(default_factory=list)


class InMemoryChoirRepository(ChoirRepository):
    """Choirs kept in the data of a unit of work."""

    def __init__(self, data: InMemoryData) -> None:
        self._data = data

    async def add(self, choir: Choir) -> None:
        self._data.choirs[choir.id] = choir

    async def get(self, choir_id: UUID) -> Choir:
        if choir_id not in self._data.choirs:
            raise ChoirNotFoundError(str(choir_id))
        return self._data.choirs[choir_id]

    async def find_by_name(self, name: str) -> Choir | None:
        key = choir_name_key(name)
        return next((c for c in self._data.choirs.values() if choir_name_key(c.name) == key), None)

    async def default(self) -> Choir | None:
        return next((c for c in self._data.choirs.values() if c.is_default), None)

    async def list(self) -> list[Choir]:
        return sorted(self._data.choirs.values(), key=lambda c: (c.created_at, c.name.casefold()))

    async def rename(self, choir_id: UUID, name: str) -> None:
        self._data.choirs[choir_id] = replace(self._data.choirs[choir_id], name=name)

    async def make_default(self, choir_id: UUID) -> None:
        for other in list(self._data.choirs.values()):
            self._data.choirs[other.id] = replace(other, is_default=other.id == choir_id)

    async def delete(self, choir_id: UUID) -> None:
        del self._data.choirs[choir_id]
        for work in [w for w in self._data.works.values() if w.choir_id == choir_id]:
            await InMemoryWorkRepository(self._data).delete(work.id)


class InMemoryWorkRepository(WorkRepository):
    """Works kept in the data of a unit of work."""

    def __init__(self, data: InMemoryData) -> None:
        self._data = data

    async def add(self, work: Work) -> None:
        self._data.works[work.id] = work

    async def get(self, work_id: UUID) -> Work:
        if work_id not in self._data.works:
            raise WorkNotFoundError(work_id)
        return self._data.works[work_id]

    async def search(self, choir_id: UUID, text: str | None = None) -> list[Work]:
        needle = search_text(text) or ""
        return [
            work
            for work in self._data.works.values()
            if work.choir_id == choir_id
            and (
                needle in (search_text(work.title) or "")
                or needle in (search_text(work.details.composer) or "")
            )
        ]

    async def count_matching(self, choir_id: UUID, text: str | None = None) -> int:
        return len(await self.search(choir_id, text))

    async def search_page(
        self, choir_id: UUID, text: str | None, offset: int, limit: int
    ) -> list[Work]:
        ordered = sorted(
            await self.search(choir_id, text),
            key=lambda work: (
                search_text(work.title) or "",
                work.details.composer is not None,
                search_text(work.details.composer) or "",
                work.id.hex,
            ),
        )
        return ordered[offset : offset + limit]

    async def update(self, work: Work) -> None:
        self._data.works[work.id] = work

    async def delete(self, work_id: UUID) -> None:
        del self._data.works[work_id]
        for score in [s for s in self._data.scores.values() if s.work_id == work_id]:
            del self._data.scores[score.id]

    async def count(self, choir_id: UUID) -> int:
        return sum(1 for work in self._data.works.values() if work.choir_id == choir_id)


class InMemoryScoreRepository(ScoreRepository):
    """Scores kept in the data of a unit of work."""

    def __init__(self, data: InMemoryData) -> None:
        self._data = data

    async def add(self, score: Score) -> None:
        if score.work_id not in self._data.works:
            raise LookupError("the work of the score does not exist (foreign key)")
        self._data.scores[score.id] = score

    async def get(self, score_id: UUID) -> Score:
        if score_id not in self._data.scores:
            raise ScoreNotFoundError(score_id)
        return self._data.scores[score_id]

    async def list(self, work_id: UUID) -> list[Score]:
        return sorted(
            (s for s in self._data.scores.values() if s.work_id == work_id),
            key=lambda s: (s.added_at, s.label, s.id),
        )

    async def list_transcriptions(self, run_id: int) -> builtins.list[Score]:
        return sorted(
            (score for score in self._data.scores.values() if score.transcription_run_id == run_id),
            key=lambda score: score.movement_number or 1,
        )

    async def list_of_choir(self, choir_id: UUID) -> builtins.list[Score]:
        return [
            score
            for score in self._data.scores.values()
            if self._data.works[score.work_id].choir_id == choir_id
        ]

    async def counts_of_works(self, work_ids: Collection[UUID]) -> dict[UUID, int]:
        counts: dict[UUID, int] = {}
        for score in self._data.scores.values():
            if score.work_id in work_ids:
                counts[score.work_id] = counts.get(score.work_id, 0) + 1
        return counts

    async def delete(self, score_id: UUID) -> None:
        del self._data.scores[score_id]

    async def storage_keys_of_work(self, work_id: UUID) -> builtins.list[str]:
        return [s.storage_key for s in self._data.scores.values() if s.work_id == work_id]

    async def storage_keys_of_choir(self, choir_id: UUID) -> builtins.list[str]:
        return [
            s.storage_key
            for s in self._data.scores.values()
            if self._data.works[s.work_id].choir_id == choir_id
        ]


class InMemoryTranscriptionRunRepository(TranscriptionRunRepository):
    """Transcription runs kept in the data of a unit of work."""

    def __init__(self, data: InMemoryData) -> None:
        self._data = data

    async def add(
        self, work_id: UUID, source_score_id: UUID, movement_count: int
    ) -> TranscriptionRun:
        run = TranscriptionRun(len(self._data.runs) + 1, work_id, source_score_id, movement_count)
        self._data.runs.append(run)
        return run

    async def latest(self, source_score_id: UUID) -> TranscriptionRun | None:
        return next(
            (run for run in reversed(self._data.runs) if run.source_score_id == source_score_id),
            None,
        )


class InMemoryDatabase:
    """Committed data, and units of work working on a copy of it."""

    def __init__(self) -> None:
        self.data = InMemoryData()
        self.commits = 0

    def unit_of_work(self) -> "InMemoryUnitOfWork":
        """New unit of work (the factory given to the services)."""
        return InMemoryUnitOfWork(self)


class InMemoryUnitOfWork(UnitOfWork):
    """Works on a copy of the data; ``commit`` publishes the copy."""

    def __init__(self, database: InMemoryDatabase) -> None:
        self._database = database
        self._data = InMemoryData()

    @property
    def choirs(self) -> InMemoryChoirRepository:
        return InMemoryChoirRepository(self._data)

    @property
    def works(self) -> InMemoryWorkRepository:
        return InMemoryWorkRepository(self._data)

    @property
    def scores(self) -> InMemoryScoreRepository:
        return InMemoryScoreRepository(self._data)

    @property
    def transcription_runs(self) -> InMemoryTranscriptionRunRepository:
        return InMemoryTranscriptionRunRepository(self._data)

    async def __aenter__(self) -> Self:
        self._data = copy.deepcopy(self._database.data)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._data = InMemoryData()

    async def start_snapshot(self, *, for_update: bool = False) -> None:
        """The double already works on a snapshot."""

    async def commit(self) -> None:
        self._database.data = copy.deepcopy(self._data)
        self._database.commits += 1
