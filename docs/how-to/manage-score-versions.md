<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Manage score versions

In personal mode, open a work to see its final scores and drafts. Every
final has a version number unique to that work. File uploads and imports
from a local file or public Google Drive link create final scores.
New MusicXML text and transcriptions create drafts.

1. Choose **Duplicate as draft** on a final MusicXML or MXL score. The
   working copy shows its date and the originating score and version.
2. Choose **Finalise score**, check the displayed name, then confirm.
   Structural validation must succeed. If the confirmation expires or
   the draft changes, review the draft again.
3. The draft moves to **Final scores** and keeps its ID and lineage.
   To change that final score, duplicate it as a draft. Confirmed deletion
   remains available and does not recycle version numbers.

With a client that can save files, choose **Download** to save the
original format. Draft file names end in ` - DRAFT` before the extension.

## Enable finalisation in your MCP Apps host

Check the host with a disposable local data directory before using it
with your repertoire. Verify that result metadata is available to the
Work view and excluded from the model, and that an app-only tool can be
called from the view but is unavailable to the model. Set
`MBC_SCORE_LIFECYCLE__TRUSTED_FINALISATION_HOST=true` in the MCP server
configuration for the verified host. The model may request a preview.
The user must click **Finalise score** to promote the draft.

## Download a PDF

Install MuseScore Studio (tested with 4.7.7 on Windows) and the existing `personal-ocr` application
extra. Configure the absolute executable path with
`MBC_SCORE_LIFECYCLE__MUSESCORE_EXECUTABLE`. Choose **Download PDF** in
the Work view. Every page of a draft PDF carries a **DRAFT** watermark.
The PDF is generated from the score document in a temporary workspace.
Linked images are unsupported by this export path. See the
[configuration reference](../configuration.md) for the export timeout.

To exercise a local installation on a two-page test score, set
`MBC_TEST_MUSESCORE_EXE` to the executable path, then run:

```sh
uv run --frozen --extra personal-ocr pytest tests/integration/test_musescore_pdf_export.py
```

## Upgrade or restore

Before upgrading, stop the personal MCP server and back up its whole
data directory, including the SQLite database and the score files.
On startup, the migration marks existing scores final and numbers them
per work. Existing files and identifiers stay intact.

To restore the previous version, stop the server and restore the entire
pre-upgrade directory before starting the previous version. Archive
the current directory first if it contains changes you need to retain.
The previous application cannot distinguish drafts, so use the saved
pre-upgrade data rather than opening the migrated data with that version.
