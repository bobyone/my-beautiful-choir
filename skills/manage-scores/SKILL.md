---
name: manage-scores
description: Use when a my-beautiful-choir user wants to add a score (PDF, MusicXML, MXL or MuseScore file) to a work of a choir's repertoire, from a file of their computer or a Google Drive link, or to open or delete a score, in personal mode.
---

<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Manage the scores of a work

Scores are managed with the tools of the my-beautiful-choir MCP server, in
personal mode. A score belongs to a work: find the work's id first (use the
`manage-works` skill to add the work if it does not exist).

## Tools

| Task | Tool |
|---|---|
| Add a score from a file of the user's computer | `add_score_from_file(work_id, path, label?)` |
| Add a score from a public Google Drive link | `add_score_from_google_drive(work_id, link, label?)` |
| Open a score | `open_score(score_id)` |
| Delete a score | `delete_score(score_id)` |

## Rules to follow

- The user can upload a file with **Add a score** in the Work view. Use
  `show_work(work_id)` to open that view. The file picker supplies the file
  to the app-only upload tool.

- Accepted formats: PDF, MusicXML (`.musicxml`), compressed MusicXML
  (`.mxl`) and MuseScore (`.mscz`), up to 50 MB. The format is recognized
  from the content, not from the file name.
- Only add a file or a link the **user asked for**; never pick a file of
  their computer on your own.
- `path` must be absolute (`~` is the user's home directory). The file is
  copied: moving or deleting it later does not affect the score.
- A Google Drive file must be shared with "Anyone with the link"; folder
  links are not supported. Tell the user that importing contacts Google,
  which sees their IP address (see the `privacy` skill).
- The label distinguishes the scores of a work ("Alto part", "Full score").
  Without a label, the file name without its extension is used.
- The same file may be added twice, for instance with two labels.
- `open_score` opens a **copy** in the default application of the computer:
  changes made there do not change the score of the repertoire.

- `delete_score` requests confirmation. If the host opens the **Deletion**
  view, ask the user to review the score and choose **Delete** or **Cancel**.

## Errors

Relay the message of the tool: it says what happened and what to do (file
not found, not a supported format, too large, not shared publicly, no
application to open the format...).
