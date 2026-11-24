# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Keep records of complete transcriptions and their movement order."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Keep older transcriptions as independent runs of one movement."""
    runs = op.create_table(
        "transcription_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "work_id", sa.Uuid(), sa.ForeignKey("works.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("source_score_id", sa.Uuid(), nullable=False),
        sa.Column("movement_count", sa.Integer(), nullable=False),
    )
    op.create_index(
        "ix_transcription_runs_source_score_id", "transcription_runs", ["source_score_id"]
    )
    # SQLite supports an inline reference on an added nullable column.
    op.execute(
        "ALTER TABLE scores ADD COLUMN transcription_run_id INTEGER "
        "REFERENCES transcription_runs (id)"
    )
    op.add_column("scores", sa.Column("movement_number", sa.Integer(), nullable=True))
    op.create_index(
        "ix_scores_transcription_run",
        "scores",
        ["transcription_run_id", "movement_number"],
        unique=True,
    )
    scores = sa.table(
        "scores",
        sa.column("id", sa.Uuid()),
        sa.column("work_id", sa.Uuid()),
        sa.column("source_score_id", sa.Uuid()),
        sa.column("content_origin", sa.String()),
        sa.column("added_at", sa.DateTime()),
        sa.column("label", sa.String()),
        sa.column("transcription_run_id", sa.Integer()),
    )
    connection = op.get_bind()
    existing = connection.execute(
        sa.select(scores.c.id, scores.c.work_id, scores.c.source_score_id)
        .where(scores.c.source_score_id.is_not(None), scores.c.content_origin == "transcription")
        .order_by(scores.c.added_at, scores.c.label, scores.c.id)
    ).all()
    for score in existing:
        run_id = connection.execute(
            runs.insert()
            .values(work_id=score.work_id, source_score_id=score.source_score_id, movement_count=1)
            .returning(runs.c.id)
        ).scalar_one()
        connection.execute(
            scores.update().where(scores.c.id == score.id).values(transcription_run_id=run_id)
        )


def downgrade() -> None:
    """Remove grouping metadata while keeping scores and their contents."""
    op.drop_index("ix_scores_transcription_run", table_name="scores")
    op.drop_column("scores", "movement_number")
    op.drop_column("scores", "transcription_run_id")
    op.drop_index("ix_transcription_runs_source_score_id", table_name="transcription_runs")
    op.drop_table("transcription_runs")
