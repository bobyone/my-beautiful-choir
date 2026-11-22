<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 17. Desktop MCP installers

- Status: accepted
- Date: 2026-11-22
- Issue: #11

## Context

Personal mode runs locally over stdio. Setting up a checkout requires
building its interface and registering the launch command in the MCP
client. The checkout and existing client settings must survive reruns.

## Decision

Provide two Python entry points backed by one installer. Reuse uv,
the lockfiles, and the existing interface build. Check the same launcher
with the MCP SDK and temporary data before configuring the client.
Use absolute paths for uv and the checkout, and launch with dependency
synchronization disabled after setup.

Use an atomic JSON update for the named Claude Desktop entry. Use the
supported Codex CLI to manage the local ChatGPT desktop entry, leaving the
other settings to Codex. An identical registration is kept. A conflicting
registration requires agreement. Client settings are handled locally and
are never printed by the installer.

## Alternatives

A single command with a client option would be more compact, but separate
entry points make the intended client explicit. Copy-and-paste setup
would avoid editing client settings automatically, but leaves the user to
build and register the application by hand.

## Consequences

The installers are for the existing personal-mode checkout workflow.
Updates remain tied to the checkout. The OpenAI entry is available to
local Codex sessions. A hosted ChatGPT integration needs a separate
design. Removing the registration reverses the client setup without
changing the repertoire or score files.
