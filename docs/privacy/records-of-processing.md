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

Personal mode runs on the user's own computer. All data stays on that
computer; the project receives nothing. The user is their own controller.

## Web mode

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
