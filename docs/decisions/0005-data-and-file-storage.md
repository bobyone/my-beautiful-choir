<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 5. Data and file storage

- Status: accepted
- Date: 2026-11-21
- Issue: #1

## Context

The application stores structured data (choirs, repertoire, accounts) and
files (scores as PDF or MusicXML, learning audio files). Personal mode runs
on a user's computer without any server; web mode serves concurrent users.

## Decision

- Structured data goes through repository abstractions, implemented with
  SQLAlchemy 2 and migrated with Alembic:
  - personal mode: SQLite, in the user's data directory;
  - web mode: PostgreSQL (psycopg 3).
- Files go through a file storage abstraction:
  - personal mode: local file system, in the user's data directory;
  - web mode: S3-compatible object storage (MinIO for development and
    `compose.yaml`), or the local file system for small deployments.
- Files are never stored in the database.

## Alternatives

- SQLite for both modes: simpler operations, but poor support for
  concurrent writes in web mode.
- Files stored in the database: simpler, but bloats the database and its
  backups.
- External links only: no storage needed, but the application cannot
  guarantee that a choir's scores stay available.

## Consequences

- Repository implementations have integration tests against SQLite and
  against PostgreSQL (testcontainers); the S3 implementation is tested
  against MinIO.
- SQL dialect differences are confined to the repository implementations.
- Backup and restore of web mode cover both the database and the object
  storage.
