<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Transcribe a PDF score in personal mode

1. Install [Audiveris](https://audiveris.github.io/audiveris/_pages/tutorials/install/binaries/)
   on the computer that runs the MCP server. The application discovers it
   automatically. See the [configuration reference](../configuration.md)
   for a custom installation.
2. Open a work with a stored PDF score and select **Transcribe the score** on
   its row. You can also ask the assistant to transcribe the named PDF of
   the work without opening the view.
3. Wait for the result. Recognition adds one MusicXML score per movement
   to the work, in PDF order, and preserves the PDF. If several PDFs match,
   choose the correct score. A movement can span several pages. If the
   engine cannot produce all movements, the application adds no scores.
4. Ask the assistant to verify the transcription against the PDF. The
   assistant can read the XML text and obtain individual page images if its
   MCP client supports them. Ask it to identify any pages it could not
   inspect. If the source PDF has been deleted, the assistant can still
   read the MusicXML and reports that the source is unavailable.

The desktop registration commands install the optional PDF rendering
dependencies. For a manual package-based personal installation, use
`uvx --from 'my-beautiful-choir[personal-ocr]' my-beautiful-choir`. From a
source checkout use `uv run --frozen --extra personal-ocr my-beautiful-choir`.
Installing this extra enables requesting source-page images.

The assistant can also save supplied MusicXML text as a new score of a
work. To rerun recognition when a transcription exists, ask explicitly
for a new transcription. Each run's movements share the date and time
they were added and appear together in the Work view. The deletion preview
shows the localized movement label and this date and time.
If a movement from the latest run was deleted, the next request transcribes
the whole PDF again and preserves the remaining scores. If recognition
fails, check the PDF or follow the engine installation link.

## Test against an installed Audiveris

Set `MBC_TEST_AUDIVERIS_PDF` to the path of a printed music PDF with at
least two pages. For a PDF with several movements, set
`MBC_TEST_AUDIVERIS_MOVEMENTS` to the expected count (the default is 1).
The test discovers Audiveris
automatically. To use a custom executable, also set
`MBC_TEST_AUDIVERIS_EXECUTABLE` to its absolute path.

```sh
uv run --frozen --extra personal-ocr pytest -q tests/integration/test_audiveris_recognition.py
```

The test skips when the score is unspecified or automatic discovery
finds no Audiveris installation. With an explicit executable, launch errors fail
the test.

## Rolling back

Before returning to a version that predates the transcription schema, make
a backup and stop the server. From a source checkout that includes
revision `0003`, run the following command with your data directory as
the last argument.

```sh
uv run --frozen python -c "import asyncio, sys; from pathlib import Path; from my_beautiful_choir.persistence.sql.sql_database import SqlDatabase; asyncio.run(SqlDatabase.in_directory(Path(sys.argv[1])).downgrade('0002'))" "<data-directory>"
```

This removes grouping and movement order metadata. The score records,
PDF and MusicXML files and source links are preserved.

## Privacy

The PDF is processed locally. Page images and XML sent in a verification
request can be passed to the model by the MCP client. See the
[records of processing](../privacy/records-of-processing.md#p3-local-transcription-and-verification).
