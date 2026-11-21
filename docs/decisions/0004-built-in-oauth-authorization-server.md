<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 4. Built-in OAuth 2.1 authorization server

- Status: accepted
- Date: 2026-11-21
- Issue: #1

## Context

In web mode, MCP clients must authenticate users. The MCP authorization
specification relies on OAuth 2.1 (authorization code with PKCE, server
metadata discovery, dynamic client registration). The project should be
deployable without additional services.

## Decision

The web mode server acts as its own OAuth 2.1 authorization server, using
the authorization framework of the official `mcp` Python SDK
(`mcp.server.auth`): the SDK implements the protocol endpoints, the project
implements the provider and the storage of clients, authorization codes and
tokens.

- Accounts are identified by e-mail address and password. Passwords are
  hashed with Argon2id (`argon2-cffi`).
- Accounts are created by invitation from an instance administrator or a
  choir manager; there is no open self-registration.
- The login page is a minimal server-rendered HTML page, internationalized
  like the UI.

## Alternatives

- External identity provider (Keycloak, generic OIDC): less security code to
  write, but one more service to deploy and operate for small choirs. It can
  be added later as another implementation of the authentication
  abstraction.
- Authorization server built with django-oauth-toolkit: mature, but brings
  Django in (see ADR 0006).

## Consequences

- The storage of OAuth artefacts is security-sensitive code: it gets
  dedicated tests and a security review in its pull request.
- Tokens are stored hashed; refresh tokens are rotated.
- Login attempts are rate-limited.
