<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Glossary

One notion, one term, used everywhere: user interface, messages,
documentation, code and API. A term is added here before it is used.

Each term shown in the user interface has a translation key: its label in
every language is in the catalogues of `ui/locales/`, and CI checks that
every key below exists. The English and French labels are given here for
reference; catalogues not yet reviewed by a native speaker are listed in
`ui/i18n/review.json`.

| Term | Definition | Code | Translation key | Label (en) | Label (fr) |
|---|---|---|---|---|---|
| Account | Identity of a person in web mode, used to sign in. | `Account` | | account | compte |
| Arranger | Author of the arrangement of a work. | `Work.arranger` | | arranger | arrangeur |
| Choir | Group of people singing together; the unit whose data is isolated from other choirs. | `Choir` | | choir | chorale |
| Chorister | Member role allowing to consult and download the choir's repertoire and scores. | `Role.CHORISTER` | | chorister | choriste |
| Composer | Author of the music of a work. | `Work.composer` | | composer | compositeur |
| Default choir | Choir used when a request names none. | `default_choir` | | default choir | chorale par défaut |
| Instance | One deployment of the application in web mode, hosting several choirs. | `Instance` | | instance | instance |
| Instance administrator | Account allowed to manage the instance, its choirs and its accounts. | `InstanceAdministrator` | | instance administrator | administrateur de l'instance |
| Manager | Member role allowing to manage the choir's repertoire, scores and members. | `Role.MANAGER` | | manager | gestionnaire |
| Membership | Link between an account and a choir, with one role. | `Membership` | | membership | adhésion |
| Mode | Way the application runs: personal mode or web mode. | `Mode` | `glossary.mode` | mode | mode |
| Personal mode | Mode where the application runs locally over stdio for a single implicit user, without accounts. | `Mode.PERSONAL` | `glossary.personalMode` | personal mode | mode perso |
| Public Google Drive link | Google Drive sharing link of a file that anyone with the link can access. | `GoogleDriveLink` | | public Google Drive link | lien Google Drive public |
| Repertoire | Set of musical works a choir sings or learns. | `Repertoire` | | repertoire | répertoire |
| Role | Rights of a member within a choir: manager or chorister. | `Role` | | role | rôle |
| Score | File holding the written music of a work (for example PDF or MusicXML). | `Score` | | score | partition |
| Score format | Type of file of a score: PDF, MusicXML, compressed MusicXML or MuseScore. | `ScoreFormat` | | format | format |
| Score label | Name distinguishing a score from the other scores of its work (for example "Alto part"). | `Score.label` | | label | libellé |
| Sung language | Language in which a work is sung. | `Work.sung_languages` | | sung language | langue chantée |
| Voicing | Distribution of voices a work is written for (for example SATB). | `Work.voicing` | | voicing | effectif vocal |
| Web mode | Mode where the application is a hosted service over HTTP, with accounts and several choirs. | `Mode.WEB` | `glossary.webMode` | web mode | mode web |
| Work | Musical work of a choir's repertoire. | `Work` | | work | œuvre |

Terms without a translation key are not shown in the user interface yet;
their key is added with the first screen that displays them.
