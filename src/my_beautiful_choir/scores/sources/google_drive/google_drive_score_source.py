# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Score downloaded from a public Google Drive link."""

import re
from email.message import Message
from email.utils import collapse_rfc2231_value, unquote
from urllib.parse import urljoin, urlsplit

import httpx

from my_beautiful_choir.scores.errors import InvalidScoreSizeError
from my_beautiful_choir.scores.sources.errors import (
    DownloadFailedError,
    NotPubliclyAccessibleError,
)
from my_beautiful_choir.scores.sources.google_drive.google_drive_link import GoogleDriveLink
from my_beautiful_choir.scores.sources.score_content import ScoreContent
from my_beautiful_choir.scores.sources.score_source import ScoreSource

ALLOWED_HOSTS = frozenset({"drive.google.com", "drive.usercontent.google.com"})
ALLOWED_HOST_SUFFIX = ".googleusercontent.com"
SIGN_IN_HOSTS = frozenset({"accounts.google.com"})
MAX_REDIRECTS = 5
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_FILE_NAME = "Google Drive file"
MAX_FILE_NAME_LENGTH = 255
NOT_ACCESSIBLE_STATUSES = frozenset({401, 403, 404})

_CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")


class GoogleDriveScoreSource(ScoreSource):
    """Downloads a file shared publicly on Google Drive.

    Only HTTPS addresses of a closed list of Google domains are contacted:
    redirects are followed one by one and checked again. A redirect to the
    Google sign-in page means that the file is not shared publicly. The
    content is requested uncompressed and read in chunks, stopping as soon as
    it exceeds the limit. The file name sent by Google is metadata only.

    The download address is not a documented API: if Google changes it, the
    download fails with ``DownloadFailedError`` or ``NotPubliclyAccessibleError``.
    """

    def __init__(
        self,
        link: GoogleDriveLink,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._link = link
        self._transport = transport
        self._timeout_seconds = timeout_seconds

    async def fetch(self, limit: int) -> ScoreContent:
        try:
            async with httpx.AsyncClient(
                transport=self._transport,
                timeout=self._timeout_seconds,
                follow_redirects=False,
                headers={"Accept-Encoding": "identity"},
            ) as client:
                return await self._download(client, limit)
        except httpx.TimeoutException as error:
            raise DownloadFailedError("Google Drive did not answer in time") from error
        except httpx.HTTPError as error:
            raise DownloadFailedError("the connection to Google Drive failed") from error

    async def _download(self, client: httpx.AsyncClient, limit: int) -> ScoreContent:
        url = self._link.download_url
        for _ in range(MAX_REDIRECTS + 1):
            async with client.stream("GET", url) as response:
                if response.is_redirect:
                    url = _next_url(response)
                    continue
                return await _read(response, limit)
        raise DownloadFailedError("Google Drive redirected too many times")


def _next_url(response: httpx.Response) -> str:
    location = response.headers.get("location")
    if not location:
        raise DownloadFailedError("Google Drive redirected without an address")
    url = urljoin(str(response.url), str(location))
    parts = urlsplit(url)
    if parts.hostname in SIGN_IN_HOSTS:
        raise NotPubliclyAccessibleError
    if not _is_allowed(url):
        raise DownloadFailedError("Google Drive redirected to an unexpected address")
    return url


def _is_allowed(url: str) -> bool:
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return False
    host = parts.hostname or ""
    return (
        parts.scheme == "https"
        and parts.username is None
        and parts.password is None
        and port in (None, 443)
        and (host in ALLOWED_HOSTS or host.endswith(ALLOWED_HOST_SUFFIX))
    )


async def _read(response: httpx.Response, limit: int) -> ScoreContent:
    if response.status_code in NOT_ACCESSIBLE_STATUSES:
        raise NotPubliclyAccessibleError
    if response.status_code != httpx.codes.OK:
        raise DownloadFailedError(f"Google Drive answered with the status {response.status_code}")
    # Google answers with a web page, not the file, when it refuses the download.
    if response.headers.get("content-type", "").lower().startswith("text/html"):
        raise NotPubliclyAccessibleError
    declared_length = response.headers.get("content-length", "")
    if declared_length.isdigit() and int(declared_length) > limit:
        raise InvalidScoreSizeError(limit)
    content = bytearray()
    async for chunk in response.aiter_raw():
        content.extend(chunk)
        if len(content) > limit:
            raise InvalidScoreSizeError(limit)
    file_name = _file_name(response.headers.get("content-disposition"))
    return ScoreContent(original_name=file_name, content=bytes(content))


def _file_name(content_disposition: str | None) -> str:
    if not content_disposition:
        return DEFAULT_FILE_NAME
    header = Message()
    header["content-disposition"] = content_disposition
    name = ""
    for key, value in header.get_params(header="content-disposition") or []:
        if key.lower() != "filename":
            continue
        if isinstance(value, tuple):
            # RFC 2231 form (filename*=UTF-8''...): preferred to the plain form.
            name = collapse_rfc2231_value(value)
            break
        name = name or unquote(value)
    name = _CONTROL_CHARACTERS.sub("", name.replace("\\", "/").rsplit("/", 1)[-1]).strip()
    return name[:MAX_FILE_NAME_LENGTH] or DEFAULT_FILE_NAME
