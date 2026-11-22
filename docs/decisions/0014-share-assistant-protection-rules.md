<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 14. Share assistant protection rules

- Status: accepted
- Date: 2026-11-22
- Issue: #8

## Context

Claude Code and Codex use different tool inputs. The project applies the
same protections to its environment files, Git hooks and remote branches.

## Decision

Both clients start the same Python module before a protected tool call.
The module adapts the action request to the shared path or command rules.
It returns exit code 2 and a fixed reason on stderr for forbidden or
malformed covered requests. It does not echo requests or inspect protected
files. The clients select the launcher in their respective repository
settings. We use uv and the Python standard library already required by the
project.

Codex also defines a workspace permission profile and Git execution rules
in its trusted repository configuration. The profile protects common
credential paths while preserving access to environment examples. The Git
rules cover direct argument prefixes. The hook checks protected shell
requests, including compound commands, and paths named in patches.

## Alternatives

Independent implementations would preserve each client's entry point at
the cost of duplicated checks and potential policy drift. Native controls
alone would not cover every supported spelling of a compound command or
the paths in a patch.

## Consequences

Hook support and permissions depend on the active Codex client and its
managed settings. Shell requests are checked for explicit protected
arguments, and the filesystem profile supplies protection independently
of the spelling when active. Repository contributors continue to follow
`CONTRIBUTING.md` and run the Git hooks.
