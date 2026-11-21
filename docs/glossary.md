<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Glossary

One notion, one term, used everywhere: user interface, messages,
documentation, code and API. A term is added here before it is used.

Labels are given in English and French for now. Labels in the other target
languages are added with the user interface translation catalogues; until
reviewed by a native speaker, they are marked *to review*.

| Term | Definition | Code | Label (en) | Label (fr) |
|---|---|---|---|---|
| Account | Identity of a person in web mode, used to sign in. | `Account` | account | compte |
| Chorister | Member role allowing to consult and download the choir's repertoire and scores. | `Role.CHORISTER` | chorister | choriste |
| Choir | Group of people singing together; the unit whose data is isolated from other choirs. | `Choir` | choir | chorale |
| Instance | One deployment of the application in web mode, hosting several choirs. | `Instance` | instance | instance |
| Instance administrator | Account allowed to manage the instance, its choirs and its accounts. | `InstanceAdministrator` | instance administrator | administrateur de l'instance |
| Manager | Member role allowing to manage the choir's repertoire, scores and members. | `Role.MANAGER` | manager | gestionnaire |
| Membership | Link between an account and a choir, with one role. | `Membership` | membership | adhésion |
| Personal mode | Mode where the application runs locally over stdio for a single implicit user, without accounts. | `PersonalMode` | personal mode | mode perso |
| Repertoire | Set of musical works a choir sings or learns. | `Repertoire` | repertoire | répertoire |
| Role | Rights of a member within a choir: manager or chorister. | `Role` | role | rôle |
| Score | File holding the written music of a work (for example PDF or MusicXML). | `Score` | score | partition |
| Web mode | Mode where the application is a hosted service over HTTP, with accounts and several choirs. | `WebMode` | web mode | mode web |
