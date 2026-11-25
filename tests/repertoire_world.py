# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Services on in-memory doubles, with a small repertoire, shared by the tests."""

from datetime import timedelta

from my_beautiful_choir.authorization.authorization import Authorization
from my_beautiful_choir.authorization.local.local_user_authorization import LocalUserAuthorization
from my_beautiful_choir.choirs.choir import Choir
from my_beautiful_choir.choirs.choir_service import ChoirService
from my_beautiful_choir.repertoire.repertoire_service import RepertoireService
from my_beautiful_choir.repertoire.work import Work, WorkDetails
from my_beautiful_choir.scores.formats.score_format_detector import ScoreFormatDetector
from my_beautiful_choir.scores.formats.signatures.pdf_signature import PdfSignature
from my_beautiful_choir.scores.musicxml.musicxml_score_validator import MusicXmlScoreValidator
from my_beautiful_choir.scores.score import Score
from my_beautiful_choir.scores.score_service import ScoreService
from tests import score_samples
from tests.doubles import FakeClock
from tests.persistence_doubles import InMemoryDatabase
from tests.score_doubles import InMemoryFileStorage, SpyScoreOpener, StubScoreSource


class RepertoireWorld:
    """Services sharing one in-memory database, file storage and clock."""

    def __init__(self) -> None:
        self.database = InMemoryDatabase()
        self.clock = FakeClock()
        self.storage = InMemoryFileStorage()
        self.opener = SpyScoreOpener()

    def choirs(self, authorization: Authorization | None = None) -> ChoirService:
        return ChoirService(
            self.database.unit_of_work,
            self.clock,
            authorization or LocalUserAuthorization(),
            self.storage,
        )

    def repertoire(self, authorization: Authorization | None = None) -> RepertoireService:
        return RepertoireService(
            self.database.unit_of_work,
            self.clock,
            authorization or LocalUserAuthorization(),
            self.storage,
        )

    def scores(self, authorization: Authorization | None = None) -> ScoreService:
        return ScoreService(
            self.database.unit_of_work,
            self.clock,
            authorization or LocalUserAuthorization(),
            self.storage,
            ScoreFormatDetector([PdfSignature()]),
            self.opener,
            validator=MusicXmlScoreValidator(),
        )

    async def choir(self, name: str) -> Choir:
        """Create a choir, one minute after the previous one."""
        self.clock.advance(timedelta(minutes=1))
        return await self.choirs().create(name)

    async def work(self, choir: str, title: str) -> Work:
        _, work = await self.repertoire().add_work(choir, WorkDetails(title=title))
        return work

    async def score(self, work: Work, label: str) -> Score:
        _, score = await self.scores().add_score(
            work.id, StubScoreSource(score_samples.pdf()), label
        )
        return score
