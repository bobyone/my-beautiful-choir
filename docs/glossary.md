<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
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
| Chorister | Member role allowing to consult and download the choir's repertoire and scores, and to see its concerts and rehearsals. | `Role.CHORISTER` | | chorister | choriste |
| Composer | Author of the music of a work. | `Work.composer` | `glossary.composer` | Composer | Compositeur |
| Concert | Event visible to everyone, including the public; its programme can be hidden from the public. | `EventKind.CONCERT` | `glossary.concert` | Concert | Concert |
| Default choir | Choir used when a request names none. | `Choir.is_default` | | default choir | chorale par défaut |
| Deletion | Removal of a choir, a work or a score with everything it contains; it cannot be undone and the user always confirms it. | `Deletion` | `glossary.deletion` | Deletion | Suppression |
| Deletion preview | Summary and record state covered by a deletion confirmation. | `DeletionPreview` | | deletion preview | aperçu de suppression |
| Detected anomaly | Musical irregularity that score reading can establish and locate. | `detected_anomaly` | | detected anomaly | anomalie détectée |
| Download | Saving of a copy of a score on the user's device through the client; the repertoire is not changed. | `download` | `work.downloadScore` | Download | Télécharger |
| Download name | File name proposed for a download: the original name without its extension, otherwise the score label, made safe for common file systems, followed by the extension of the score format. | `download_name` | | download name | nom de téléchargement |
| Draft date | Creation date of a draft, displayed in the user's time zone. | `draft_date` (`Score.added_at`) | | draft date | date du brouillon |
| Draft score | Dated, editable score of a work that can be finalised. | `ScoreState.DRAFT` | `work.draftScore` | Draft | Brouillon |
| DRAFT watermark | Visible DRAFT marking applied to every page of a PDF exported from a draft. | `PdfWatermarker.mark_draft` | | DRAFT | DRAFT |
| Duplication as a draft | Creation of an independent draft from a final score in the same work. | `duplicate_as_draft` | `work.duplicateDraft` | Duplicate as draft | Dupliquer en brouillon |
| Event | Dated occasion of a choir: a concert, a rehearsal or a lesson. | `Event` | `glossary.event` | Event | Événement |
| Event kind | Nature of an event, which sets who may see it: concert, rehearsal or lesson. It never changes. | `EventKind` | | event kind | nature d'événement |
| Exchange notation | Versioned compact representation of measures, their events and effective attributes. | `notation_version` | | exchange notation | notation d’échange |
| Final score | Numbered score with immutable content and metadata. It can be deleted after confirmation. | `ScoreState.FINAL` | `work.finalScore` | Final | Finale |
| Finalisation | Promotion of a validated draft to a final score after explicit user confirmation. | `finalise` | `work.finaliseScore` | Finalise score | Finaliser la partition |
| Hidden programme | State of a concert whose programme is not shown to the public; members still see it. | `Event.programme_hidden` | | hidden programme | programme masqué |
| Instance | One deployment of the application in web mode, hosting several choirs. | `Instance` | | instance | instance |
| Instance administrator | Account allowed to manage the instance, its choirs and its accounts. | `InstanceAdministrator` | | instance administrator | administrateur de l'instance |
| Instrument | Singing voice or instrument associated with the events of a part. | `Part.instruments` | | instrument | instrument |
| Lesson | Event visible to its participants and to the managers. | `EventKind.LESSON` | `glossary.lesson` | Lesson | Cours |
| Manager | Member role allowing to manage the choir's repertoire, scores, events and members. | `Role.MANAGER` | | manager | gestionnaire |
| Match | One-to-one association of parts or measures when comparing scores. | `Match` | | match | correspondance |
| Measure | Ordered segment of a part with a printed label that may recur. | `Measure` | | measure | mesure |
| Measure range | Contiguous measures of one part, including both endpoints. | `read_measures` | | measure range | plage de mesures |
| Membership | Link between an account and a choir, with one role. | `Membership` | | membership | adhésion |
| Mode | Way the application runs: personal mode or web mode. | `Mode` | `glossary.mode` | mode | mode |
| Movement | Section of a source score, possibly starting or ending within a page. | `movement_number` | `glossary.movement` | Movement {number} | Mouvement {number} |
| Notes | Optional information about a work. | `Work.notes` | `glossary.notes` | Notes | Notes |
| Observer | Person consulting events: a member, the instance administrator, the local user or the public. | `Observer` | | observer | observateur |
| Original name | Name of the file of a score when it was added; metadata only, never used as a path, and kept unchanged. | `Score.original_name` | | original name | nom d'origine |
| Originating score | Final score from which a draft was duplicated. Its label and version are kept if it is deleted. | `OriginatingScore` | `work.originatingScore` | From {label} v{versionNumber} | D’après {label} v{versionNumber} |
| Part | Ordered measures intended for one or more performers and possibly containing several staves and voices. | `Part` | | part | partie |
| Participant | Member of the choir who is given access to a lesson. | `Event.participant_ids` | | participant | participant |
| PDF export | Rendering a score copy to PDF for download. Each page of a draft PDF carries the DRAFT watermark. | `ScorePdfExporter.export` | `work.downloadPdf` | Download PDF | Télécharger le PDF |
| Period | Time interval, both bounds included, used to list events. | `Period` | | period | période |
| Personal mode | Mode where the application runs locally over stdio for a single implicit user, without accounts. | `Mode.PERSONAL` | `glossary.personalMode` | personal mode | mode perso |
| Programme | Ordered list of programme entries of an event. | `Event.programme` | | programme | programme |
| Programme entry | Position in a programme that refers to a work, or to none, with an optional note. It keeps the title of the work. | `ProgrammeEntry` | | programme entry | entrée de programme |
| Public | People who are not members of a choir. | `ObserverKind.PUBLIC` | | public | public |
| Public Google Drive link | Google Drive sharing link of a file that anyone with the link can access. | `GoogleDriveLink` | | public Google Drive link | lien Google Drive public |
| Rehearsal | Event visible to all members of the choir. | `EventKind.REHEARSAL` | `glossary.rehearsal` | Rehearsal | Répétition |
| Repertoire | Set of musical works a choir sings or learns. | `Repertoire` | `glossary.repertoire` | Repertoire | Répertoire |
| Repertoire page | Ordered slice of the works of a choir matching a search, with its number, its size (10 works by default, at most 100) and the number of matching works. | `RepertoirePage` | `repertoire.pages` | Repertoire pages | Pages du répertoire |
| Role | Rights of a member within a choir: manager or chorister. | `Role` | | role | rôle |
| Score | File holding the written music of a work (for example PDF or MusicXML). | `Score` | `glossary.score` | Score | Partition |
| Score format | Type of file of a score: PDF, MusicXML, compressed MusicXML or MuseScore. | `ScoreFormat` | `glossary.scoreFormat` | Format | Format |
| Score label | Name distinguishing a score from the other scores of its work (for example "Alto part"). | `Score.label` | `glossary.scoreLabel` | Label | Libellé |
| Score origin | Where the content of a score came from when it was added: the file picker of a view, a local file on the user's computer, a public Google Drive link, MusicXML text submitted by the model, or a transcription. | `ScoreOrigin` | | origin | origine |
| Score size | Number of bytes in the stored score. | `Score.size` | `glossary.scoreSize` | Size | Taille |
| Server registration | Settings that tell a client how to start the local MCP server. | `ClientRegistration` | | server registration | inscription du serveur |
| Sounding pitch | Pitch after the transposition declared for the instrument has been applied. | `MusicalEvent.sounding` | | sounding pitch | hauteur entendue |
| Source score | Existing PDF score of a work used to generate a transcription. | `source_score_id` | | source score | partition source |
| Stale confirmation | Confirmation whose deletion preview differs from the current state. | `StaleConfirmationError` | | stale confirmation | confirmation périmée |
| Sung language | Language in which a work is sung. | `Work.sung_languages` | `glossary.sungLanguage` | Sung language | Langue chantée |
| Title | Required name of a work. | `Work.title` | `glossary.title` | Title | Titre |
| Transcription | MusicXML score produced by optical recognition of one movement of a source score. | `TranscriptionJob` | `glossary.transcription` | Transcription | Transcription |
| Transcription run | One completed processing of a source score, with its expected number of movements. | `TranscriptionRun` | | transcription run | lancement de transcription |
| Validation report | Errors found when validating a draft. Errors block finalisation. | `ValidationReport` | | validation report | rapport de validation |
| Version number | Increasing number of a final score, unique in its work and never reused. | `Score.version_number` | | version number | numéro de version |
| Verification | Comparison of a transcription with its source score to identify differences and report the passages inspected. | | | verification | vérification |
| Voicing | Distribution of voices a work is written for (for example SATB). | `Work.voicing` | `glossary.voicing` | Voicing | Effectif vocal |
| Web mode | Mode where the application is a hosted service over HTTP, with accounts and several choirs. | `Mode.WEB` | `glossary.webMode` | web mode | mode web |
| Work | Musical work of a choir's repertoire. | `Work` | `glossary.work` | Work | Œuvre |
| Work reference | A complete catalogue reference written in the title of a work, such as NL15.2. | `work_reference` | | work reference | référence de l'œuvre |
| Written pitch | Pitch as notated, including its spelling and alteration. | `Pitch` | | written pitch | hauteur écrite |

Terms without a translation key are not shown in the user interface yet;
their key is added with the first screen that displays them.

## Contribution

| Term | Definition | Code |
|---|---|---|
| Action request | The proposed action and any resource it targets. | `check_request` input |
| Protection rule | A condition an action request must satisfy before it proceeds. | `protection_rules` |
