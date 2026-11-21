<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 9. Licensing and contributions

- Status: accepted
- Date: 2026-11-21
- Issue: #1

## Context

The repository is public and ships the GNU GPL version 2 licence text. The
licence identifier must be explicit, compatible with common dependencies,
and contributions must be traceable.

## Decision

- The project is licensed under `GPL-2.0-or-later`.
- The repository follows the REUSE specification: every file carries an
  SPDX header naming `bobyone` as copyright holder, or is covered by
  `REUSE.toml` when it cannot hold a header.
- Contributors add an `SPDX-FileContributor` line with their forge account
  to files they create or significantly modify, and are listed in
  `CONTRIBUTORS.md`.
- Contributions are certified with the Developer Certificate of Origin:
  every commit carries a `Signed-off-by` line, checked by CI.

## Alternatives

- `GPL-2.0-only`: incompatible with Apache-2.0 dependencies, common in both
  the Python and JavaScript ecosystems.
- `AGPL-3.0-or-later`: would require hosted modifications to be published,
  but changes the licence chosen for the repository.
- Contributor License Agreement: allows relicensing, but discourages
  contributions.

## Consequences

- CI checks REUSE compliance and the licence compatibility of every Python
  and npm dependency.
