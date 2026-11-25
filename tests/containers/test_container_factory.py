# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the dependency assembly of each mode."""

from pathlib import Path

import pytest
from dependency_injector import providers

from my_beautiful_choir import __version__
from my_beautiful_choir.application.application import Application
from my_beautiful_choir.configuration.mode import Mode
from my_beautiful_choir.configuration.settings import Settings
from my_beautiful_choir.configuration.web_settings import WebSettings
from my_beautiful_choir.containers.container_factory import create_container
from my_beautiful_choir.monitoring.null_metrics import NullMetrics
from my_beautiful_choir.monitoring.prometheus.prometheus_metrics import PrometheusMetrics
from my_beautiful_choir.monitoring.server.server_health_check import ServerHealthCheck
from my_beautiful_choir.persistence.sql.prepare_data_store import PrepareDataStore
from my_beautiful_choir.persistence.sql.sql_database import SqlDatabase
from my_beautiful_choir.scores.formats.score_format import ScoreFormat
from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.scores.sources.google_drive.google_drive_link import GoogleDriveLink
from my_beautiful_choir.scores.sources.google_drive.google_drive_score_source import (
    GoogleDriveScoreSource,
)
from my_beautiful_choir.storage.file_system.local_file_storage import LocalFileStorage
from my_beautiful_choir.tools.metered_tool import MeteredTool
from my_beautiful_choir.transport.http.http_transport import HttpTransport
from my_beautiful_choir.transport.stdio.stdio_transport import StdioTransport
from tests import score_samples


def test_personal_mode_assembly() -> None:
    container = create_container(Settings(mode=Mode.PERSONAL))
    assert isinstance(container.application(), Application)
    assert isinstance(container.mode.transport(), StdioTransport)
    assert isinstance(container.mode.metrics(), NullMetrics)
    info = container.application_info()
    assert (info.name, info.version, info.mode) == (
        "my-beautiful-choir",
        __version__,
        Mode.PERSONAL,
    )


def test_web_mode_assembly_uses_the_web_settings() -> None:
    container = create_container(Settings(mode=Mode.WEB, web=WebSettings(port=1234)))
    transport = container.mode.transport()
    assert isinstance(transport, HttpTransport)
    assert transport.address == ("127.0.0.1", 1234)
    assert isinstance(container.mode.metrics(), PrometheusMetrics)
    assert isinstance(container.mode.health_check(), ServerHealthCheck)
    assert container.application_info().mode is Mode.WEB


def test_tools_are_metered_with_the_mode_metrics() -> None:
    container = create_container(Settings(mode=Mode.WEB))
    [tool] = container.tools()
    assert isinstance(tool, MeteredTool)
    assert tool.name == "show_about"
    assert container.mode.metrics() is container.mode.metrics()


def test_singletons_are_shared_within_a_container() -> None:
    container = create_container(Settings())
    assert container.application() is container.application()


def test_overrides_stay_within_their_container() -> None:
    overridden = create_container(Settings())
    overridden.mode.transport.override(providers.Object("fake"))
    assert overridden.mode.transport() == "fake"
    assert isinstance(create_container(Settings()).mode.transport(), StdioTransport)


def test_personal_mode_prepares_its_data_store(tmp_path: Path) -> None:
    container = create_container(Settings(mode=Mode.PERSONAL, data_dir=tmp_path))
    [step] = container.mode.startup_steps()
    assert isinstance(step, PrepareDataStore)
    database = container.mode.database()
    assert isinstance(database, SqlDatabase)
    assert database.engine.url.database == str(tmp_path / "my-beautiful-choir.sqlite3")
    assert container.mode.database() is database


def test_personal_mode_stores_files_in_its_data_directory(tmp_path: Path) -> None:
    container = create_container(Settings(mode=Mode.PERSONAL, data_dir=tmp_path))
    file_storage = container.mode.file_storage()
    assert isinstance(file_storage, LocalFileStorage)
    assert file_storage.root == tmp_path / "files"
    assert container.mode.file_storage() is file_storage


@pytest.mark.parametrize(
    ("content", "score_format"),
    [
        (score_samples.pdf(), ScoreFormat.PDF),
        (score_samples.musicxml(), ScoreFormat.MUSICXML),
        (score_samples.compressed_musicxml(), ScoreFormat.COMPRESSED_MUSICXML),
        (score_samples.musescore(), ScoreFormat.MUSESCORE),
    ],
)
def test_personal_mode_recognizes_every_score_format(
    content: bytes, score_format: ScoreFormat
) -> None:
    detector = create_container(Settings(mode=Mode.PERSONAL)).mode.score_format_detector()
    assert detector.detect(content) is score_format


def test_personal_mode_downloads_from_google_drive_with_a_new_source() -> None:
    container = create_container(Settings(mode=Mode.PERSONAL))
    link = GoogleDriveLink("1aBcD_eFgH-ijKlMnOpQrStUvWxYz0123")
    first = container.mode.google_drive_source(link)
    assert isinstance(first, GoogleDriveScoreSource)
    assert first.link == link.url
    assert container.mode.google_drive_source(link) is not first
    assert isinstance(container.mode.score_service(), ScoreService)


def test_web_mode_has_no_startup_step() -> None:
    assert list(create_container(Settings(mode=Mode.WEB)).mode.startup_steps()) == []


def test_personal_mode_offers_the_repertoire_tools(tmp_path: Path) -> None:
    container = create_container(Settings(mode=Mode.PERSONAL, data_dir=tmp_path))
    names = [tool.name for tool in container.tools()]
    assert names == [
        "show_about",
        "describe_score",
        "read_measures",
        "compare_scores",
        "duplicate_score_as_draft",
        "preview_score_finalisation",
        "confirm_score_finalisation",
        "download_score_pdf",
        "find_score_sources",
        "transcribe_score",
        "get_transcription_status",
        "add_musicxml_score",
        "read_musicxml_score",
        "read_score_source_page",
        "list_choirs",
        "create_choir",
        "rename_choir",
        "set_default_choir",
        "add_work",
        "edit_work",
        "add_score_from_file",
        "add_score_from_google_drive",
        "open_score",
        "get_score_file",
        "list_scores",
        "show_repertoire",
        "show_work",
        "upload_score",
        "download_score",
        "preview_work_deletion",
        "preview_score_deletion",
        "delete_choir",
        "delete_work",
        "delete_score",
        "confirm_deletion",
    ]
    assert all(isinstance(tool, MeteredTool) for tool in container.tools())


def test_web_mode_offers_no_repertoire_tool() -> None:
    container = create_container(Settings(mode=Mode.WEB))
    assert [tool.name for tool in container.tools()] == ["show_about"]
