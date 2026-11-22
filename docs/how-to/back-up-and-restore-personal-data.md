<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Back up and restore personal data

Use this procedure in personal mode. The data directory contains
`my-beautiful-choir.sqlite3` and the `files/` directory that holds the scores.
The [configuration reference](../configuration.md#keys) lists its default
locations. If you configured `MBC_DATA_DIR`, use that directory.

## Back up

1. Quit the MCP client completely and make sure the personal-mode server
   has stopped. If more than one client uses the same data directory,
   stop all of them.
2. Copy the **whole** data directory to a new backup directory. The
   database and stored scores must be taken together. Keep the backup
   private and, if appropriate, encrypted.
3. Start the MCP client again. Keep the copy until the next successful
   backup has been verified.

## Restore

1. Stop every client using the data directory. Back up the current data
   first so you can undo the restoration.
2. Confirm that you want to restore the selected backup. Move the current
   directory aside and copy the backup into its place. Avoid combining
   files from different backups.
3. Start the client, show the repertoire and open a score to check that
   both the database and score storage are available.
4. To undo the restoration, stop the client and put the moved directory
   back. An older application version may require a backup from before a
   database migration.
