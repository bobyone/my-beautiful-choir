# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Number existing scores and persist score states and lineage."""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make every existing score final and number it within its work."""
    op.add_column(
        "scores", sa.Column("state", sa.String(5), nullable=False, server_default="final")
    )
    op.add_column("scores", sa.Column("version_number", sa.Integer))
    op.add_column("scores", sa.Column("draft_revision", sa.Integer))
    op.add_column("scores", sa.Column("originating_score_id", sa.Uuid))
    op.add_column("scores", sa.Column("originating_score_label", sa.String(100)))
    op.add_column("scores", sa.Column("originating_score_version", sa.Integer))
    op.create_table(
        "score_version_counters",
        sa.Column(
            "work_id", sa.Uuid, sa.ForeignKey("works.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column("last_number", sa.Integer, nullable=False),
    )
    op.execute(
        """
        WITH numbered AS (
            SELECT id, row_number() OVER (
                PARTITION BY work_id ORDER BY added_at,
                    CASE WHEN movement_number IS NOT NULL THEN transcription_run_id END,
                    movement_number, label, id
            ) AS number
            FROM scores
        )
        UPDATE scores
        SET version_number = (SELECT number FROM numbered WHERE numbered.id = scores.id)
        """
    )
    op.execute(
        """
        INSERT INTO score_version_counters (work_id, last_number)
        SELECT work_id, max(version_number) FROM scores GROUP BY work_id
        """
    )
    op.create_index("ix_scores_work_version", "scores", ["work_id", "version_number"], unique=True)


def downgrade() -> None:
    """Drop lifecycle metadata, preserving score records and files."""
    op.drop_index("ix_scores_work_version", table_name="scores")
    op.drop_table("score_version_counters")
    for name in (
        "originating_score_version",
        "originating_score_label",
        "originating_score_id",
        "draft_revision",
        "version_number",
        "state",
    ):
        op.drop_column("scores", name)
