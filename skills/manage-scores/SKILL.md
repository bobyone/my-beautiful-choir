---
name: manage-scores
description: Use when a my-beautiful-choir user wants to add a score (PDF, MusicXML, MXL or MuseScore file) to a work of a choir's repertoire, from a file of their computer or a Google Drive link, or to transcribe a stored PDF, add or read MusicXML text, verify a transcription against its PDF, open, receive or delete a score in personal mode.
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
| Find scores without opening a view | `list_scores(work_id?, work_title?, work_reference?, choir?)` |
| Send a score to the user in the conversation | `get_score_file(score_id)` |
| Delete a score | `delete_score(score_id)` |

## Rules to follow

- When the user asks to open a work or use the file picker, call
  `show_work(work_id)`. In the Work view, **Add a score** supplies the file
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
- `get_score_file` gives the file back in the conversation, whatever its size.
  Whether the user can save it depends on the client. The file is named by
  its download name: the original name without its extension (otherwise the
  label), with characters that file systems refuse replaced by `_`, followed
  by the extension of the detected format (for instance `Alto.mscz` holding a
  PDF is given as `Alto.pdf`). The original name stays in the repertoire.
  A large score uses much of the conversation context. If the client cannot
  present the embedded file, explain that the user can ask to open the score
  locally or use **Download** in the Work view.

- `delete_score` requests confirmation. If the host opens the **Deletion**
  view, ask the user to review the score and choose **Delete** or **Cancel**.
  If the deletion preview changes, review it again before confirming.

## Send scores in the conversation

1. Call `list_scores` for each named work using exactly one of `work_id`,
   `work_title` or `work_reference`. Use `work_reference` for a complete
   reference in the title, such as `NL15.2`. For a title or reference search,
   provide the choir if named. Otherwise, the search uses the default choir.
2. Choose the requested scores by label and format. If several works or
   scores could satisfy the request, ask which ones the user wants. If a
   work or score is missing, report it.
3. Call `get_score_file` for each unambiguous score, including in a request
   with other scores still to clarify. Keep the conversation view-free
   unless the user asks to open a view.

## Transcribe and verify

- Call `find_score_sources` with the work id or title, an optional choir
  and an optional score label. This needs no view. Ask which work or PDF
  to use if several match the user's request.
- Call `transcribe_score(score_id)` directly. The Work view is optional.
  When the result is pending, wait before calling
  `get_transcription_status(job_id)` again. Specify `recompute: true` only
  when the user asks for another transcription. Read the complete ordered
  `scores` array. Each movement is a score linked to the same source PDF.
  Relay the official
  installation link when the engine is missing or unavailable.
- Read the score with `read_musicxml_score(score_id, offset?, length?)`,
  following the returned `next_offset` for more text. To verify the score
  when the user asks, use `read_score_source_page(score_id, page)` on
  the returned source score id if it is available. For several movements,
  follow their returned order when comparing with the PDF. If the source was
  deleted, report that the comparison is unavailable. Otherwise, compare
  with the actual pages, report
  differences and identify any passages you could not check.
- Use `add_musicxml_score(work_id, xml, label?)` to add the actual XML
  text when the user asks you to save it.

## Errors

Relay the message of the tool: it says what happened and what to do (file
not found, not a supported format, too large, not shared publicly, no
application to open the format...).
