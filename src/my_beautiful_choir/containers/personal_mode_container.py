# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Assembly specific to personal mode."""

from importlib.resources.abc import Traversable
from typing import Any

from dependency_injector import containers, providers

from my_beautiful_choir.authorization.local.local_user_authorization import LocalUserAuthorization
from my_beautiful_choir.choirs.choir_service import ChoirService
from my_beautiful_choir.clock.system_clock import SystemClock
from my_beautiful_choir.configuration.settings import Settings
from my_beautiful_choir.confirmation.memory.in_memory_pending_confirmations import (
    InMemoryPendingConfirmations,
)
from my_beautiful_choir.deletion.deletion_preview import DeletionPreview
from my_beautiful_choir.monitoring.null_metrics import NullMetrics
from my_beautiful_choir.persistence.sql.prepare_data_store import PrepareDataStore
from my_beautiful_choir.persistence.sql.sql_database import SqlDatabase
from my_beautiful_choir.repertoire.repertoire_service import RepertoireService
from my_beautiful_choir.scores.formats.score_format_detector import ScoreFormatDetector
from my_beautiful_choir.scores.formats.signatures.music_xml_signature import MusicXmlSignature
from my_beautiful_choir.scores.formats.signatures.pdf_signature import PdfSignature
from my_beautiful_choir.scores.formats.signatures.zip.compressed_music_xml_signature import (
    CompressedMusicXmlSignature,
)
from my_beautiful_choir.scores.formats.signatures.zip.muse_score_signature import (
    MuseScoreSignature,
)
from my_beautiful_choir.scores.opening.system.system_score_opener import SystemScoreOpener
from my_beautiful_choir.scores.score_service import ScoreService
from my_beautiful_choir.scores.sources.google_drive.google_drive_score_source import (
    GoogleDriveScoreSource,
)
from my_beautiful_choir.scores.sources.uploaded_score_source import UploadedScoreSource
from my_beautiful_choir.storage.file_system.local_file_storage import LocalFileStorage
from my_beautiful_choir.tools.choirs.create_choir_tool import CreateChoirTool
from my_beautiful_choir.tools.choirs.list_choirs_tool import ListChoirsTool
from my_beautiful_choir.tools.choirs.rename_choir_tool import RenameChoirTool
from my_beautiful_choir.tools.choirs.set_default_choir_tool import SetDefaultChoirTool
from my_beautiful_choir.tools.metered_tool import MeteredTool
from my_beautiful_choir.tools.repertoire.add_work_tool import AddWorkTool
from my_beautiful_choir.tools.repertoire.edit_work_tool import EditWorkTool
from my_beautiful_choir.tools.scores.add_score_from_file_tool import AddScoreFromFileTool
from my_beautiful_choir.tools.scores.add_score_from_google_drive_tool import (
    AddScoreFromGoogleDriveTool,
)
from my_beautiful_choir.tools.scores.get_score_file_tool import GetScoreFileTool
from my_beautiful_choir.tools.scores.open_score_tool import OpenScoreTool
from my_beautiful_choir.tools.tool import Tool
from my_beautiful_choir.tools.view_tool.deletion.confirm_deletion_tool import (
    ConfirmDeletionTool,
)
from my_beautiful_choir.tools.view_tool.deletion.delete_choir_tool import DeleteChoirTool
from my_beautiful_choir.tools.view_tool.deletion.delete_score_tool import DeleteScoreTool
from my_beautiful_choir.tools.view_tool.deletion.delete_work_tool import DeleteWorkTool
from my_beautiful_choir.tools.view_tool.repertoire.show_repertoire_tool import ShowRepertoireTool
from my_beautiful_choir.tools.view_tool.work.preview_deletion_from_work_view_tool import (
    PreviewDeletionFromWorkViewTool,
)
from my_beautiful_choir.tools.view_tool.work.show_work_tool import ShowWorkTool
from my_beautiful_choir.tools.view_tool.work.upload_score_tool import UploadScoreTool
from my_beautiful_choir.transport.stdio.stdio_transport import StdioTransport
from my_beautiful_choir.views.packaged.packaged_view import PackagedView


def _metered(
    tool: type[Tool[Any]], metrics: providers.Provider[Any], **dependencies: providers.Provider[Any]
) -> providers.Singleton[MeteredTool[Any]]:
    """Provider of ``tool``, built with ``dependencies`` and wrapped to record its metrics."""
    return providers.Singleton(
        MeteredTool, inner=providers.Singleton(tool, **dependencies), metrics=metrics
    )


class PersonalModeContainer(containers.DeclarativeContainer):
    """Personal mode: stdio transport, no metrics, SQLite database in the data directory."""

    settings = providers.Dependency(instance_of=Settings)

    metrics = providers.Singleton(NullMetrics)
    transport = providers.Singleton(StdioTransport)

    data_dir = settings.provided.data_dir
    database = providers.Singleton(SqlDatabase.in_directory, data_dir=data_dir)
    startup_steps = providers.List(
        providers.Singleton(PrepareDataStore, data_dir=data_dir, database=database)
    )
    unit_of_work = database.provided.unit_of_work
    file_storage = providers.Singleton(LocalFileStorage.in_directory, data_dir=data_dir)

    # MuseScore files also hold a MusicXML container: they are recognized first.
    score_format_detector = providers.Singleton(
        ScoreFormatDetector,
        signatures=providers.List(
            providers.Singleton(PdfSignature),
            providers.Singleton(MuseScoreSignature),
            providers.Singleton(CompressedMusicXmlSignature),
            providers.Singleton(MusicXmlSignature),
        ),
    )

    clock = providers.Singleton(SystemClock)
    pending_confirmations = providers.Singleton[InMemoryPendingConfirmations[DeletionPreview]](
        InMemoryPendingConfirmations, clock=clock
    )
    conversation_confirmations = providers.Singleton[
        InMemoryPendingConfirmations[tuple[str, DeletionPreview]]
    ](InMemoryPendingConfirmations, clock=clock)

    # The directory of the common views, given by create_container.
    views_directory: providers.Dependency[Traversable] = providers.Dependency()
    deletion_view = providers.Singleton(PackagedView, name="deletion", directory=views_directory)
    repertoire_view = providers.Singleton(
        PackagedView, name="repertoire", directory=views_directory
    )
    work_view = providers.Singleton(PackagedView, name="work", directory=views_directory)
    authorization = providers.Singleton(LocalUserAuthorization)

    choir_service = providers.Singleton(
        ChoirService,
        unit_of_work=unit_of_work,
        clock=clock,
        authorization=authorization,
        file_storage=file_storage,
    )

    repertoire_service = providers.Singleton(
        RepertoireService,
        unit_of_work=unit_of_work,
        clock=clock,
        authorization=authorization,
        file_storage=file_storage,
    )

    score_opener = providers.Singleton(SystemScoreOpener.in_temporary_directory)
    google_drive_source = providers.Factory(GoogleDriveScoreSource)
    uploaded_score_source = providers.Factory(UploadedScoreSource)

    score_service = providers.Singleton(
        ScoreService,
        unit_of_work=unit_of_work,
        clock=clock,
        authorization=authorization,
        file_storage=file_storage,
        format_detector=score_format_detector,
        opener=score_opener,
    )

    mode_tools = providers.List(
        _metered(ListChoirsTool, metrics, service=choir_service),
        _metered(CreateChoirTool, metrics, service=choir_service),
        _metered(RenameChoirTool, metrics, service=choir_service),
        _metered(SetDefaultChoirTool, metrics, service=choir_service),
        _metered(AddWorkTool, metrics, service=repertoire_service),
        _metered(EditWorkTool, metrics, service=repertoire_service),
        _metered(AddScoreFromFileTool, metrics, service=score_service),
        _metered(
            AddScoreFromGoogleDriveTool,
            metrics,
            service=score_service,
            source_factory=google_drive_source.provider,
        ),
        _metered(OpenScoreTool, metrics, service=score_service),
        _metered(GetScoreFileTool, metrics, service=score_service),
        _metered(
            ShowRepertoireTool,
            metrics,
            view=repertoire_view,
            repertoire=repertoire_service,
            choirs=choir_service,
        ),
        _metered(
            ShowWorkTool,
            metrics,
            view=work_view,
            repertoire=repertoire_service,
            scores=score_service,
        ),
        _metered(
            UploadScoreTool,
            metrics,
            view=work_view,
            service=score_service,
            source_factory=uploaded_score_source.provider,
        ),
        _metered(
            PreviewDeletionFromWorkViewTool,
            metrics,
            view=work_view,
            deleter=repertoire_service,
            pending=pending_confirmations,
        ),
        _metered(
            PreviewDeletionFromWorkViewTool,
            metrics,
            view=work_view,
            deleter=score_service,
            pending=pending_confirmations,
        ),
        _metered(
            DeleteChoirTool,
            metrics,
            view=deletion_view,
            service=choir_service,
            pending=pending_confirmations,
            conversation=conversation_confirmations,
        ),
        _metered(
            DeleteWorkTool,
            metrics,
            view=deletion_view,
            deleter=repertoire_service,
            pending=pending_confirmations,
            conversation=conversation_confirmations,
        ),
        _metered(
            DeleteScoreTool,
            metrics,
            view=deletion_view,
            deleter=score_service,
            pending=pending_confirmations,
            conversation=conversation_confirmations,
        ),
        _metered(
            ConfirmDeletionTool,
            metrics,
            view=deletion_view,
            deleters=providers.List(choir_service, repertoire_service, score_service),
            pending=pending_confirmations,
        ),
    )
