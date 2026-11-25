# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Add the events of the choirs and their programmes (issue #30)."""

import sqlalchemy as sa
from alembic import op

from my_beautiful_choir.persistence.sql.utc_date_time import UtcDateTime

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the events and programme entries tables; existing data is unchanged."""
    op.create_table(
        "events",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "choir_id",
            sa.Uuid,
            sa.ForeignKey("choirs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("starts_at", UtcDateTime, nullable=False),
        sa.Column("ends_at", UtcDateTime),
        sa.Column("place", sa.String(200)),
        sa.Column("notes", sa.Text),
        sa.Column("programme_hidden", sa.Boolean, nullable=False),
        sa.Column("created_at", UtcDateTime, nullable=False),
        sa.Column("updated_at", UtcDateTime, nullable=False),
    )
    op.create_index("ix_events_choir_start", "events", ["choir_id", "starts_at"])
    op.create_table(
        "programme_entries",
        sa.Column(
            "event_id",
            sa.Uuid,
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("position", sa.Integer, primary_key=True),
        sa.Column(
            "work_id", sa.Uuid, sa.ForeignKey("works.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("work_title", sa.String(200)),
        sa.Column("note", sa.String(200)),
    )
    op.create_index("ix_programme_entries_work_id", "programme_entries", ["work_id"])


def downgrade() -> None:
    """Drop the events and their programmes; nothing else is touched."""
    op.drop_index("ix_programme_entries_work_id", table_name="programme_entries")
    op.drop_table("programme_entries")
    op.drop_index("ix_events_choir_start", table_name="events")
    op.drop_table("events")
