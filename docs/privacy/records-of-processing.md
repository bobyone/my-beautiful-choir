<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Records of processing

This document describes the personal data processing performed by
my-beautiful-choir, to help the organization that deploys it (the
controller) keep its own records of processing under Article 30 of the
GDPR. It is updated in the same commit as any code that changes a
processing.

> **Draft.** This document must be reviewed by a legal professional. It is
> not legal advice.

## Personal mode

Personal mode runs on the user's own computer. The project receives no
application data. The user controls their local data.
The server stores its data locally. It can contact Google Drive at the
user's request (P1). The MCP client handles tool calls and view content
as described in P2.

### P1. Score import from a public Google Drive link (implemented)

| Item | Description |
|---|---|
| Purpose | Copy into the user's repertoire a score file the user shared publicly on Google Drive, at the user's request. |
| Legal basis | The user acts for themselves (household use); for a choir, legitimate interest of the controller in collecting its scores — Art. 6(1)(f) GDPR. |
| Data subjects | The user importing the score. |
| Data categories | Sent to Google: the IP address of the user's computer, the id of the Google Drive file and the usual technical HTTP headers. No account, cookie, name or e-mail address is sent. Received: the file and its name, stored on the user's computer with the link. |
| Recipients | Google (Google Drive), which receives the request. |
| Processors | None: Google acts as the provider of the file the user chose to share, under its own terms. |
| Transfers outside the EU | Possible: Google may serve the request from servers outside the EU, under its own privacy policy. |
| Retention | Nothing is kept by the software beyond the imported score, kept until the user deletes it. Google's retention of its request logs is set by Google. |
| Security measures | HTTPS only; only a closed list of Google Drive domains is contacted, checked again on every redirect; time limit; download stopped beyond 50 MB; the file name sent by Google is never used as a path; nothing is downloaded without a request from the user. |

### P2. Local repertoire and scores (implemented)

| Item | Description |
|---|---|
| Purpose | Manage the user's choirs, works and scores in personal mode. |
| Legal basis | The user acts for themselves (household use). A choir using the software determines its own lawful basis. |
| Data subjects | The user and any people named in work metadata or score files. |
| Data categories | Choir names, work titles, composer, arranger, voicing, sung languages, notes, score metadata and file content. |
| Recipients | The local server and the selected MCP client. The content of a score can be returned to the client in a tool result (`get_score_file`, up to the 50 MB score maximum); the client may pass it to its model, hence to the model provider. Users should check how their MCP client handles tool calls, results and view content. |
| Processors and transfers outside the EU | The application stores this data locally. Any separate processing by the MCP client is governed by its own configuration and terms. See P1 for public Google Drive imports. |
| Retention | The application keeps the records until the user deletes them. A confirmed deletion removes the affected records and score files. Deletion previews and tokens are held in server memory, valid for up to ten minutes, and cleared on restart. The user manages the retention of separately made backups. |
| Security measures | The database and scores use a user data directory. File storage paths are based on generated UUIDs. Opening a score creates a copy in a private temporary directory. Score uploads have content and size validation, and destructive actions require confirmation. |

### P3. Local transcription and verification (implemented)

| Item | Description |
|---|---|
| Purpose | Generate a transcription from a PDF score, and let the user ask the model to compare the transcription with the source. |
| Legal basis | Same as P2. |
| Data subjects and categories | Same as P2. A transcription also stores the identifier of its source score. |
| Recipients and processors | The local engine reads a temporary PDF copy. When requested, the selected MCP client receives MusicXML text or rendered PDF pages and may pass them to its model provider. |
| Transfers outside the EU | None by recognition itself. The chosen MCP client's configuration and terms govern its handling of requested tool results. |
| Retention | Transcriptions remain in the repertoire until deleted. Temporary recognition files are removed at the end of a normal run. Flatpak receives access to the per-job directory in the application cache only. The server keeps up to 32 recent job statuses in memory. |
| Security measures | Local batch execution, private temporary workspace, bounded score and tool response sizes, authorization through the score service and XML parsing without fetching external resources. |

## Web mode

### 0. Technical logs and metrics (implemented)

| Item | Description |
|---|---|
| Purpose | Operate the service: diagnose failures, measure load and errors. |
| Legal basis | Legitimate interest of the controller in running a secure and available service — Art. 6(1)(f) GDPR. |
| Data subjects | People using an MCP client connected to the instance. |
| Data categories | None identifying a person: HTTP method, route, status code, duration, random correlation id. **Client IP addresses are not logged** (the uvicorn access log is disabled). Metrics are aggregated counters without any identifier. |
| Recipients | The instance operator. |
| Processors | Hosting provider of the instance, chosen by the controller. |
| Transfers outside the EU | None by the software. |
| Retention | Logs are written to stderr; their retention is set by the controller's log collection. |
| Security measures | No personal data in logs by design; no secret is ever logged. |

The processing below is planned by the design validated in
[issue #1](https://github.com/bobyone/my-beautiful-choir/issues/1); it is
detailed when implemented.

### 1. Account management and authentication

| Item | Description |
|---|---|
| Purpose | Allow members of choirs to sign in and use the service according to their role. |
| Legal basis | Performance of a contract (terms of use) — Art. 6(1)(b) GDPR. |
| Data subjects | Instance administrators, choir managers and choristers. |
| Data categories | E-mail address, display name, password hash (Argon2id), memberships and roles, OAuth tokens (stored hashed), preferred language. |
| Recipients | The instance operator; within a choir, its managers. |
| Processors | Hosting provider of the instance, chosen by the controller. |
| Transfers outside the EU | None by the software. Depends on the hosting chosen by the controller. |
| Retention | Account data: until account deletion. Tokens: until expiry or revocation. Retention periods are configured by the controller. |
| Security measures | Password hashing (Argon2id), hashed tokens, rate-limited sign-in, TLS, per-choir data isolation. |

### 2. Repertoire and scores

| Item | Description |
|---|---|
| Purpose | Share the choir's repertoire and scores among its members. |
| Legal basis | Performance of a contract (terms of use) — Art. 6(1)(b) GDPR. |
| Data subjects | Choir members uploading files. |
| Data categories | Uploaded files and their author (the uploading account). |
| Recipients | Members of the same choir. |
| Processors | Hosting and object storage provider, chosen by the controller. |
| Transfers outside the EU | None by the software. |
| Retention | Until deleted by a manager, or until the choir is deleted. |
| Security measures | Per-choir access control, TLS. |
