# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Alembic environment: migrations run on the connection given by SqlDatabase."""

from alembic import context

from my_beautiful_choir.persistence.sql.tables import metadata

connection = context.config.attributes.get("connection")
if connection is None:
    raise RuntimeError("Migrations run through SqlDatabase.migrate(), with a connection")

context.configure(connection=connection, target_metadata=metadata, render_as_batch=True)
with context.begin_transaction():
    context.run_migrations()
