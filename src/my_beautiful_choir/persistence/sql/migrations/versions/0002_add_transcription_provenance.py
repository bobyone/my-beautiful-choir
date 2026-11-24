# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Record the provenance of MusicXML scores."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add nullable metadata while keeping older scores intact."""
    op.add_column("scores", sa.Column("source_score_id", sa.Uuid(), nullable=True))
    op.add_column("scores", sa.Column("content_origin", sa.String(20), nullable=True))


def downgrade() -> None:
    """Remove provenance metadata while retaining all score data."""
    op.drop_column("scores", "content_origin")
    op.drop_column("scores", "source_score_id")
