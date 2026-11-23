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
| Arranger | Author of the arrangement of a work. | `Work.arranger` | `glossary.arranger` | Arranger | Arrangeur |
| Choir | Group of people singing together; the unit whose data is isolated from other choirs. | `Choir` | `glossary.choir` | Choir | Chorale |
| Chorister | Member role allowing to consult and download the choir's repertoire and scores. | `Role.CHORISTER` | | chorister | choriste |
| Composer | Author of the music of a work. | `Work.composer` | `glossary.composer` | Composer | Compositeur |
| Default choir | Choir used when a request names none. | `Choir.is_default` | | default choir | chorale par défaut |
| Deletion | Removal of a choir, a work or a score with everything it contains; it cannot be undone and the user always confirms it. | `Deletion` | `glossary.deletion` | Deletion | Suppression |
| Deletion preview | Summary and record state covered by a deletion confirmation. | `DeletionPreview` | | deletion preview | aperçu de suppression |
| Download | Saving of a copy of a score on the user's device through the client; the repertoire is not changed. | `download` | `work.downloadScore` | Download | Télécharger |
| Instance | One deployment of the application in web mode, hosting several choirs. | `Instance` | | instance | instance |
| Instance administrator | Account allowed to manage the instance, its choirs and its accounts. | `InstanceAdministrator` | | instance administrator | administrateur de l'instance |
| Manager | Member role allowing to manage the choir's repertoire, scores and members. | `Role.MANAGER` | | manager | gestionnaire |
| Membership | Link between an account and a choir, with one role. | `Membership` | | membership | adhésion |
| Mode | Way the application runs: personal mode or web mode. | `Mode` | `glossary.mode` | mode | mode |
| Personal mode | Mode where the application runs locally over stdio for a single implicit user, without accounts. | `Mode.PERSONAL` | `glossary.personalMode` | personal mode | mode perso |
| Notes | Optional information about a work. | `Work.notes` | `glossary.notes` | Notes | Notes |
| Original name | Name of the file of a score when it was added; metadata only, never used as a path, given back as the file name of a download. | `Score.original_name` | | original name | nom d'origine |
| Public Google Drive link | Google Drive sharing link of a file that anyone with the link can access. | `GoogleDriveLink` | | public Google Drive link | lien Google Drive public |
| Repertoire | Set of musical works a choir sings or learns. | `Repertoire` | `glossary.repertoire` | Repertoire | Répertoire |
| Repertoire page | Ordered slice of the works of a choir matching a search, with its number, its size (10 works by default, at most 100) and the number of matching works. | `RepertoirePage` | `repertoire.pages` | Repertoire pages | Pages du répertoire |
| Role | Rights of a member within a choir: manager or chorister. | `Role` | | role | rôle |
| Score | File holding the written music of a work (for example PDF or MusicXML). | `Score` | `glossary.score` | Score | Partition |
| Score format | Type of file of a score: PDF, MusicXML, compressed MusicXML or MuseScore. | `ScoreFormat` | `glossary.scoreFormat` | Format | Format |
| Score label | Name distinguishing a score from the other scores of its work (for example "Alto part"). | `Score.label` | `glossary.scoreLabel` | Label | Libellé |
| Score origin | Where the content of a score came from when it was added: the file picker of a view, a local file of the user's computer, or a public Google Drive link. | `ScoreOrigin` | | origin | origine |
| Score size | Number of bytes in the stored score. | `Score.size` | `glossary.scoreSize` | Size | Taille |
| Stale confirmation | Confirmation whose deletion preview differs from the current state. | `StaleConfirmationError` | | stale confirmation | confirmation périmée |
| Server registration | Settings that tell a client how to start the local MCP server. | `ClientRegistration` | | server registration | inscription du serveur |
| Sung language | Language in which a work is sung. | `Work.sung_languages` | `glossary.sungLanguage` | Sung language | Langue chantée |
| Title | Required name of a work. | `Work.title` | `glossary.title` | Title | Titre |
| Voicing | Distribution of voices a work is written for (for example SATB). | `Work.voicing` | `glossary.voicing` | Voicing | Effectif vocal |
| Web mode | Mode where the application is a hosted service over HTTP, with accounts and several choirs. | `Mode.WEB` | `glossary.webMode` | web mode | mode web |
| Work | Musical work of a choir's repertoire. | `Work` | `glossary.work` | Work | Œuvre |

Terms without a translation key are not shown in the user interface yet;
their key is added with the first screen that displays them.

## Contribution

| Term | Definition | Code |
|---|---|---|
| Action request | The proposed action and any resource it targets. | `check_request` input |
| Protection rule | A condition an action request must satisfy before it proceeds. | `protection_rules` |
