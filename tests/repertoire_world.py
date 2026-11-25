# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Services on in-memory doubles, with a small repertoire, shared by the tests."""

from collections.abc import Sequence
from datetime import datetime, timedelta

from my_beautiful_choir.authorization.authorization import Authorization
from my_beautiful_choir.authorization.local.local_user_authorization import LocalUserAuthorization
from my_beautiful_choir.authorization.observer_source import ObserverSource
from my_beautiful_choir.choirs.choir import Choir
from my_beautiful_choir.choirs.choir_service import ChoirService
from my_beautiful_choir.configuration.event_settings import EventSettings
from my_beautiful_choir.events.event import Event, EventDetails
from my_beautiful_choir.events.event_kind import EventKind
from my_beautiful_choir.events.event_service import EventService
from my_beautiful_choir.events.programme_item import ProgrammeItem
from my_beautiful_choir.repertoire.repertoire_service import RepertoireService
from my_beautiful_choir.repertoire.work import Work, WorkDetails
from my_beautiful_choir.scores.formats.score_format_detector import ScoreFormatDetector
from my_beautiful_choir.scores.formats.signatures.music_xml_signature import MusicXmlSignature
from my_beautiful_choir.scores.formats.signatures.pdf_signature import PdfSignature
from my_beautiful_choir.scores.musicxml.musicxml_score_validator import MusicXmlScoreValidator
from my_beautiful_choir.scores.score import Score
from my_beautiful_choir.scores.score_service import ScoreService
from tests import score_samples
from tests.doubles import FakeClock, StubObserverSource
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
            ScoreFormatDetector([PdfSignature(), MusicXmlSignature()]),
            self.opener,
            validator=MusicXmlScoreValidator(),
        )

    def events(
        self,
        authorization: Authorization | None = None,
        observers: ObserverSource | None = None,
    ) -> EventService:
        return EventService(
            self.database.unit_of_work,
            self.clock,
            authorization or LocalUserAuthorization(),
            observers or StubObserverSource(),
            EventSettings(),
        )

    async def event(
        self,
        choir: str,
        title: str,
        starts_at: datetime,
        kind: EventKind = EventKind.CONCERT,
        works: Sequence[Work] = (),
    ) -> Event:
        _, event = await self.events().create_event(
            choir,
            kind,
            EventDetails(title=title, starts_at=starts_at),
            [ProgrammeItem(work.id) for work in works],
        )
        return event

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
