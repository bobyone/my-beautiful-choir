<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 6. Python server stack

- Status: accepted
- Date: 2026-11-21
- Issue: #1

## Context

The server must be written in Python. It must follow a layered
architecture with dependency injection, run over stdio and Streamable HTTP,
and be checked by the same commands locally and in CI.

## Decision

| Concern | Tool |
|---|---|
| Language | Python 3.14 |
| MCP server | official `mcp` SDK (FastMCP API), Starlette, uvicorn |
| Dependency injection | `dependency-injector` (declarative containers, configuration from environment and files) |
| Persistence | SQLAlchemy 2, Alembic, psycopg 3 |
| Object storage | `boto3` |
| Password hashing | `argon2-cffi` |
| Static typing | mypy (strict) |
| Package manager, lock file | uv, `uv.lock` |
| Dependency audit | `pip-audit` |
| Tests, doubles, coverage | pytest, `unittest.mock`, pytest-cov, testcontainers |
| Lint and format | ruff |
| Task runner | nox (single definition of the commands used by the pre-commit hook and CI) |
| Pre-commit hook | pre-commit |
| Internationalization | Babel (gettext catalogues, CLDR formats) |
| Logs | standard `logging`, JSON output with `python-json-logger` |
| Correlation id | `asgi-correlation-id` (web mode) |
| Metrics | `prometheus-client` (web mode) |
| Licence compliance | `reuse`, `pip-licenses` |

Configuration is read once at the entry point (environment variables and an
optional configuration file) and injected through the container.

## Alternatives

- Standalone FastMCP library: richer ergonomics (middlewares, in-memory
  client, auth providers), but a third-party layer over the official SDK
  with frequent breaking changes.
- Django with django-oauth-toolkit: mature authorization server, migrations
  and i18n, but its conventions couple the domain to the ORM and it is heavy
  for a stdio process.
- `dishka` as container: modern and async-friendly, but less established
  than `dependency-injector`.

## Consequences

- The OAuth provider storage must be implemented by the project (see
  ADR 0004).
- Package versions are pinned in `uv.lock`; tool versions used by CI are
  pinned in the workflows.
