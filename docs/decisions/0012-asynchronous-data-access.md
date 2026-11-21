<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 12. Asynchronous data access

- Status: accepted
- Date: 2026-11-21
- Issue: #7

## Context

[ADR 0005](0005-data-and-file-storage.md) chose SQLAlchemy 2 and Alembic,
with SQLite in personal mode and PostgreSQL in web mode. MCP tools run in
an asynchronous server (anyio), and one operation (for instance deleting a
choir with its works and scores) must be atomic.

## Decision

- The core accesses data through a **Unit of Work** giving the
  repositories (`UnitOfWork`), opened as an asynchronous context and
  committed explicitly; any exception rolls it back.
- The SQL implementation uses **SQLAlchemy's asyncio extension**, with the
  `aiosqlite` driver for SQLite (psycopg 3 in asynchronous mode for
  PostgreSQL, when web mode stores data).
- Case- and accent-insensitive search uses normalized search columns,
  computed when writing, so that SQLite and PostgreSQL behave the same.
- Identifiers are UUIDs.
- Personal mode migrates its database with Alembic at startup.

## Alternatives

- Synchronous SQLAlchemy run in worker threads: no extra driver, but a unit
  of work spread over threads is fragile and every call needs a thread hop.
- The standard `sqlite3` module without an ORM: no dependency, but SQL
  written twice (SQLite and PostgreSQL) and no migrations.
- Database-specific accent folding (a custom SQLite function, PostgreSQL
  `unaccent`): no extra columns, but two behaviours to test.

## Consequences

- New dependencies: `sqlalchemy[asyncio]` (with `greenlet`), `alembic`,
  `aiosqlite`.
- Repository implementations have integration tests on SQLite now, and on
  PostgreSQL when web mode stores data.
- A failed migration prevents startup (`MBC-DATA`) instead of running on an
  inconsistent schema.
