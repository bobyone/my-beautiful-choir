# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Create choirs, works and scores.

Revision ID: 0001
Revises:
Create Date: 2026-11-21 19:06:29.139321
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "choirs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("name_key", sa.String(length=100), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_choirs")),
        sa.UniqueConstraint("name_key", name=op.f("uq_choirs_name_key")),
    )
    with op.batch_alter_table("choirs", schema=None) as batch_op:
        batch_op.create_index(
            "ix_choirs_single_default",
            ["is_default"],
            unique=True,
            sqlite_where=sa.text("is_default"),
            postgresql_where=sa.text("is_default"),
        )

    op.create_table(
        "works",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("choir_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("title_search", sa.String(length=200), nullable=False),
        sa.Column("composer", sa.String(length=200), nullable=True),
        sa.Column("composer_search", sa.String(length=200), nullable=True),
        sa.Column("arranger", sa.String(length=200), nullable=True),
        sa.Column("voicing", sa.String(length=50), nullable=True),
        sa.Column("sung_languages", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["choir_id"], ["choirs.id"], name=op.f("fk_works_choir_id_choirs"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_works")),
    )
    with op.batch_alter_table("works", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_works_choir_id"), ["choir_id"], unique=False)

    op.create_table(
        "scores",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("work_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("format", sa.String(length=20), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("origin", sa.String(length=20), nullable=False),
        sa.Column("link", sa.String(length=2048), nullable=True),
        sa.Column("storage_key", sa.String(length=200), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["work_id"], ["works.id"], name=op.f("fk_scores_work_id_works"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scores")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_scores_storage_key")),
    )
    with op.batch_alter_table("scores", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_scores_work_id"), ["work_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("scores", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_scores_work_id"))

    op.drop_table("scores")
    with op.batch_alter_table("works", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_works_choir_id"))

    op.drop_table("works")
    with op.batch_alter_table("choirs", schema=None) as batch_op:
        batch_op.drop_index(
            "ix_choirs_single_default",
            sqlite_where=sa.text("is_default"),
            postgresql_where=sa.text("is_default"),
        )

    op.drop_table("choirs")
