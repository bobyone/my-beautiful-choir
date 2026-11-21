# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Origins of the content of a score."""

from enum import StrEnum


class ScoreOrigin(StrEnum):
    """Where the content of a score came from when it was added."""

    FILE_PICKER = "file_picker"
    """Chosen by the user with the file picker of a view."""

    LOCAL_FILE = "local_file"
    """Read from a file of the user's computer, named by its path."""

    GOOGLE_DRIVE = "google_drive"
    """Downloaded from a public Google Drive link, which is kept with the score."""
