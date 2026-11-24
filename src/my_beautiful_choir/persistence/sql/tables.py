# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Database schema; every change comes with an Alembic migration."""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    Uuid,
)

from my_beautiful_choir.persistence.sql.utc_date_time import UtcDateTime

CHOIR_NAME_LENGTH = 100
WORK_TEXT_LENGTH = 200
VOICING_LENGTH = 50
NOTES_LENGTH = 2000
SCORE_LABEL_LENGTH = 100
ORIGINAL_NAME_LENGTH = 255
LINK_LENGTH = 2048

metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

choirs = Table(
    "choirs",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("name", String(CHOIR_NAME_LENGTH), nullable=False),
    Column("name_key", String(CHOIR_NAME_LENGTH), nullable=False, unique=True),
    Column("is_default", Boolean, nullable=False),
    Column("created_at", UtcDateTime, nullable=False),
)
Index(
    "ix_choirs_single_default",
    choirs.c.is_default,
    unique=True,
    sqlite_where=choirs.c.is_default,
    postgresql_where=choirs.c.is_default,
)

works = Table(
    "works",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "choir_id", Uuid, ForeignKey("choirs.id", ondelete="CASCADE"), nullable=False, index=True
    ),
    Column("title", String(WORK_TEXT_LENGTH), nullable=False),
    # Normalized for searching (case-folded, without accents): see search_text().
    Column("title_search", String(WORK_TEXT_LENGTH), nullable=False),
    Column("composer", String(WORK_TEXT_LENGTH)),
    Column("composer_search", String(WORK_TEXT_LENGTH)),
    Column("arranger", String(WORK_TEXT_LENGTH)),
    Column("voicing", String(VOICING_LENGTH)),
    Column("sung_languages", JSON, nullable=False),
    Column("notes", Text),
    Column("created_at", UtcDateTime, nullable=False),
    Column("updated_at", UtcDateTime, nullable=False),
)

transcription_runs = Table(
    "transcription_runs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("work_id", Uuid, ForeignKey("works.id", ondelete="CASCADE"), nullable=False),
    Column("source_score_id", Uuid, nullable=False, index=True),
    Column("movement_count", Integer, nullable=False),
)

scores = Table(
    "scores",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("work_id", Uuid, ForeignKey("works.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("label", String(SCORE_LABEL_LENGTH), nullable=False),
    Column("format", String(20), nullable=False),
    Column("size", Integer, nullable=False),
    Column("original_name", String(ORIGINAL_NAME_LENGTH), nullable=False),
    Column("origin", String(20), nullable=False),
    Column("link", String(LINK_LENGTH)),
    Column("storage_key", String(200), nullable=False, unique=True),
    Column("added_at", UtcDateTime, nullable=False),
    Column("source_score_id", Uuid),
    Column("content_origin", String(20)),
    Column("transcription_run_id", Integer, ForeignKey("transcription_runs.id")),
    Column("movement_number", Integer),
)
Index(
    "ix_scores_transcription_run",
    scores.c.transcription_run_id,
    scores.c.movement_number,
    unique=True,
)
