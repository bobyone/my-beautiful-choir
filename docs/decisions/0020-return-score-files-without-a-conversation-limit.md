<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 20. Return score files without a conversation limit

- Status: accepted
- Date: 2026-11-24
- Issue: #18
- Supersedes: the 2 MiB conversation limit of
  [ADR 0019](0019-return-score-files-as-embedded-resources.md); the rest of
  ADR 0019 stays in force.

## Context

ADR 0019 limited the scores returned by `get_score_file` to 2 MiB, because
a returned file may enter the model context, and kept that limit on the
app-only `download_score` for clients that do not declare MCP Apps support.
Users want to receive any of their scores in the conversation; the 50 MB
score maximum already bounds what is stored.

## Decision

- `get_score_file` and `download_score` return any stored score, with no
  limit other than the 50 MB score maximum.
- What only served the limit is removed: the conversation limit constant,
  `ScoreTooLargeToReturnError`, `ScoreAboveLimitError`, the maximum size of
  `ScoreService.read_score` and `FileStorage.read`, and
  `ToolContext.client_shows_views`.
- The tool description gives no size warning to the model; the
  `manage-scores` skill advises `open_score` or the Work view for large
  scores.

## Alternatives considered

- **Keep the limit parameters and pass no limit**: leaves a mechanism
  nothing uses. Rejected.
- **Warn the model in the tool description**: rejected by the maintainer.

## Consequences

- A score of up to 50 MB, about 67 MB of base64, may enter the model
  context of hosts that pass embedded resources to the model, or be refused
  by the host.
- Reading a score always loads its whole content.
