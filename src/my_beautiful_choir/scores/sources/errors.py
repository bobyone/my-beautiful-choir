# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Exceptions of the score sources."""

from pathlib import Path

from my_beautiful_choir.scores.errors import ScoresError


class ScoreSourceError(ScoresError):
    """The content of a score cannot be obtained from its source."""


class UnreadableLocalFileError(ScoreSourceError):
    """A local file does not exist, is not a regular file or cannot be read."""

    def __init__(self, path: Path, reason: str) -> None:
        super().__init__(
            f"The file {path} cannot be read: {reason}. Check the path, which must be "
            "absolute, and that the file can be read by your user."
        )
        self.path = path
        self.reason = reason


class UnsupportedLinkError(ScoreSourceError):
    """A link is not the link of a Google Drive file over HTTPS."""

    def __init__(self, link: str) -> None:
        super().__init__(
            f"The link {link!r} is not supported. Give the sharing link of a Google Drive "
            "file, such as https://drive.google.com/file/d/<id>/view; folder links and "
            "other sites are not supported."
        )
        self.link = link


class NotPubliclyAccessibleError(ScoreSourceError):
    """A Google Drive file does not exist or is not shared publicly."""

    def __init__(self) -> None:
        super().__init__(
            "The Google Drive file does not exist or is not shared publicly. In Google Drive, "
            'share it with "Anyone with the link", or download it and add it as a file.'
        )


class DownloadFailedError(ScoreSourceError):
    """A file cannot be downloaded."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            f"The file cannot be downloaded: {reason}. Check the connection and try again, "
            "or download the file and add it as a file."
        )
        self.reason = reason
