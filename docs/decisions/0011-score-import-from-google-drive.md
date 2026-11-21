<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 11. Score import from Google Drive

- Status: accepted
- Date: 2026-11-21
- Issue: #7

## Context

At the framing of the project (#1), the answer was "no integrations with
existing systems". Choirs, however, often share their scores through public
Google Drive links, and a manager wants to add such a score to a work
without downloading it first.

## Decision

- A score can be added from a **public Google Drive link** to a file. The
  file is **copied** into the file storage, with the same format and size
  checks as any other score; the link is kept as the origin of the score.
- Only file links are accepted, over HTTPS, on `drive.google.com`. The
  download follows redirects only to a closed list of Google domains, with
  timeouts, and stops as soon as the file exceeds the size limit.
- A file that is not shared publicly is refused with a clear error; no
  Google account is ever used.
- The download is isolated in one adapter (`GoogleDriveScoreSource`): the
  download address used is not a documented Google API.
- This is the only integration; other storage services and arbitrary HTTPS
  links are out of scope.

## Alternatives

- Keep only the link and open it in the browser: no storage, but the score
  disappears when the sharing is removed, and cannot be opened offline
  ([ADR 0005](0005-data-and-file-storage.md) rejected external links as the
  only storage).
- Accept any HTTPS link: more general, but widens the attack surface
  (server-side request forgery in web mode) for a need not expressed.
- Google Drive API with OAuth: reaches private files, but requires a Google
  Cloud project, credentials and a consent screen.

## Consequences

- When a score is imported, the user's computer (personal mode) or the
  instance (web mode) contacts Google, which sees its IP address and the
  file id. This is declared in the records of processing.
- A change of Google's download address breaks the import with a clear
  error, and is fixed in the adapter only.
- Tests never use the network: the HTTP transport is replaced by a double.
