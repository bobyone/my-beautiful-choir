# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Link to a Google Drive file."""

import re
from dataclasses import dataclass
from typing import Self
from urllib.parse import parse_qs, urlencode, urlsplit

from my_beautiful_choir.scores.sources.errors import UnsupportedLinkError

HOST = "drive.google.com"
DOWNLOAD_URL = "https://drive.usercontent.google.com/download"

_ID = r"[A-Za-z0-9_-]{10,200}"
_FILE_PATH = re.compile(rf"/file(?:/u/\d+)?/d/(?P<id>{_ID})(?:/[A-Za-z]*)?/?")
_QUERY_PATHS = frozenset({"/open", "/uc"})
_ID_ONLY = re.compile(_ID)


@dataclass(frozen=True)
class GoogleDriveLink:
    """Identifies a Google Drive file, and the resource key some older shared files require."""

    file_id: str
    resource_key: str | None = None

    @classmethod
    def parse(cls, link: str) -> Self:
        """Link from a Google Drive file URL over HTTPS; raises ``UnsupportedLinkError``.

        Accepted: ``https://drive.google.com/file/d/<id>/view`` (and its
        variants ``/edit``, ``/preview``, ``/file/u/<n>/d/<id>``), ``/open?id=<id>``
        and ``/uc?id=<id>``. Folders, Google Docs and other sites are refused.
        """
        try:
            parts = urlsplit(link.strip())
            port = parts.port
        except ValueError as error:
            raise UnsupportedLinkError(link) from error
        if (
            parts.scheme != "https"
            or parts.hostname != HOST
            or parts.username is not None
            or parts.password is not None
            or port not in (None, 443)
        ):
            raise UnsupportedLinkError(link)
        query = parse_qs(parts.query)
        file_id = _file_id(parts.path, query)
        if file_id is None:
            raise UnsupportedLinkError(link)
        resource_keys = query.get("resourcekey", [])
        resource_key = resource_keys[0] if resource_keys else None
        if resource_key is not None and _ID_ONLY.fullmatch(resource_key) is None:
            raise UnsupportedLinkError(link)
        return cls(file_id=file_id, resource_key=resource_key)

    @property
    def url(self) -> str:
        """Canonical sharing link of the file, as kept with its score."""
        url = f"https://{HOST}/file/d/{self.file_id}/view"
        if self.resource_key is not None:
            url += "?" + urlencode({"resourcekey": self.resource_key})
        return url

    @property
    def download_url(self) -> str:
        """Address downloading the content of the file, without the virus scan warning page."""
        parameters = {"id": self.file_id, "export": "download", "confirm": "t"}
        if self.resource_key is not None:
            parameters["resourcekey"] = self.resource_key
        return f"{DOWNLOAD_URL}?{urlencode(parameters)}"


def _file_id(path: str, query: dict[str, list[str]]) -> str | None:
    match = _FILE_PATH.fullmatch(path)
    if match is not None:
        return match["id"]
    if path in _QUERY_PATHS:
        ids = query.get("id", [])
        if len(ids) == 1 and _ID_ONLY.fullmatch(ids[0]) is not None:
            return ids[0]
    return None
