<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 10. Packaging and deployment

- Status: accepted
- Date: 2026-11-21
- Issue: #1

## Context

Personal mode is launched by an MCP client on the user's computer (Windows,
macOS or Linux). Web mode is a hosted service whose deployment target is
not chosen yet; the expected volume is small (a few dozen choirs, a few
thousand users, one application instance).

## Decision

- Personal mode is distributed as a Python package on PyPI, launched with
  `uvx`, published by CI with PyPI trusted publishing (OIDC).
- Web mode is distributed as a container image on GHCR, built once by CI
  per release and promoted unchanged between environments.
- `compose.yaml` runs web mode with PostgreSQL and MinIO, for development
  and small deployments.
- Deployment commands (`deploy`, `rollback`, `review-env`) are nox sessions,
  taking the environment and the version as parameters.
- The declarative deployment tool is deferred to the ADR that will choose
  the deployment target.
- Pull requests are tested locally (`gh pr checkout`, then the quick-start
  command).
- CI runs the full Windows, macOS and Linux matrix on pull requests and on
  the main branch.

## Alternatives

- Desktop extension bundle (`.mcpb`): one-click install in Claude Desktop,
  but specific to one host; it can be added later.
- Kubernetes with review environments per pull request: premature without
  a chosen target.

## Consequences

- Releases (tag `vX.Y.Z`) publish the PyPI package, the GHCR image, the
  GitHub Release and the Claude Code plugin at the same version.
- The image runs as a non-root user and exposes a health check.
