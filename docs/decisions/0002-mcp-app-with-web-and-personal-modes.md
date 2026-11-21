<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 2. MCP app with a web mode and a personal mode

- Status: accepted
- Date: 2026-11-21
- Issue: #1

## Context

my-beautiful-choir manages choirs from within an AI assistant. It has no
standalone user interface: it is used only through MCP clients. Two usages
are needed:

- a shared, hosted service, where the members of several choirs work
  together, with accounts and administration;
- a private usage, where a single person manages their own choirs on their
  own computer, without any server.

## Decision

The application is delivered only as an **MCP app**: an MCP server whose
tools are complemented by interactive interfaces declared as MCP Apps
resources (`ui://`), rendered by the MCP client.

The same application core runs in two modes, selected at the entry point:

- **web mode**: Streamable HTTP transport, user accounts, authentication
  (see ADR 0004), several choirs per instance (see ADR 0003);
- **personal mode**: stdio transport, launched by the MCP client, with a
  single implicit local user who manages every local choir; no account, no
  authentication, no administration.

Business logic only depends on abstractions (current user, authorization,
storage). Each mode provides its own implementations, assembled at the
entry point.

The UI targets any host implementing the MCP Apps extension. Every tool
also returns a text result, so that clients without MCP Apps support remain
usable.

## Alternatives

- A classic web application with an MCP server on the side: duplicates the
  user interface and contradicts the product goal.
- Two separate applications: duplicates the business logic.
- Targeting Claude only: simpler testing, but ties the project to one host.

## Consequences

- The only HTML page served outside the MCP app is the OAuth login page of
  web mode, required by the browser-based authorization flow.
- In stdio mode, logs must go to stderr: stdout carries the MCP protocol.
- Tests cover both modes for every feature whose behaviour depends on the
  mode (identity, authorization).
