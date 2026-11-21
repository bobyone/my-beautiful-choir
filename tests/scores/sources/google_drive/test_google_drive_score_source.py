# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Integration tests of the Google Drive download, with a mocked HTTP transport."""

from collections.abc import AsyncIterator, Callable

import httpx
import pytest

from my_beautiful_choir.scores.errors import InvalidScoreSizeError
from my_beautiful_choir.scores.sources.errors import (
    DownloadFailedError,
    NotPubliclyAccessibleError,
)
from my_beautiful_choir.scores.sources.google_drive.google_drive_link import GoogleDriveLink
from my_beautiful_choir.scores.sources.google_drive.google_drive_score_source import (
    GoogleDriveScoreSource,
)
from my_beautiful_choir.scores.sources.score_content import ScoreContent
from tests import score_samples

LINK = GoogleDriveLink(file_id="1aBcD_eFgH-ijKlMnOpQrStUvWxYz0123")
LIMIT = 1024
PDF_HEADERS = {
    "content-type": "application/pdf",
    "content-disposition": (
        'attachment; filename="Ave Maria.pdf"; '
        "filename*=UTF-8''Ave%20Maria%20%E2%80%93%20SATB.pdf"
    ),
}

Handler = Callable[[httpx.Request], httpx.Response]


async def _streamed(data: bytes) -> AsyncIterator[bytes]:
    """Body sent in chunks, as by a real server, rather than read in advance."""
    for start in range(0, len(data), 512):
        yield data[start : start + 512]


async def _fetch(handler: Handler, limit: int = LIMIT) -> ScoreContent:
    return await GoogleDriveScoreSource(LINK, transport=httpx.MockTransport(handler)).fetch(limit)


def _redirect(location: str) -> httpx.Response:
    return httpx.Response(303, headers={"location": location})


@pytest.mark.anyio
async def test_downloads_a_public_file() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, headers=PDF_HEADERS, content=_streamed(score_samples.pdf()))

    fetched = await _fetch(handler)
    assert fetched == ScoreContent(
        original_name="Ave Maria \u2013 SATB.pdf", content=score_samples.pdf()
    )
    [request] = requests
    assert str(request.url) == LINK.download_url
    assert request.headers["accept-encoding"] == "identity"


@pytest.mark.anyio
async def test_follows_the_redirects_within_google_drive() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "drive.usercontent.google.com":
            return _redirect("https://doc-0s-9k-docs.googleusercontent.com/docs/file")
        if request.url.path == "/docs/file":
            return _redirect("/docs/file2")
        return httpx.Response(200, content=_streamed(b"content"))

    fetched = await _fetch(handler)
    assert fetched == ScoreContent(original_name="Google Drive file", content=b"content")


@pytest.mark.anyio
@pytest.mark.parametrize(
    "location",
    [
        "https://accounts.google.com/ServiceLogin?continue=https://drive.google.com",
        "https://accounts.google.com/v3/signin/identifier",
    ],
)
async def test_a_private_file_leads_to_the_sign_in_page(location: str) -> None:
    with pytest.raises(NotPubliclyAccessibleError):
        await _fetch(lambda request: _redirect(location))


@pytest.mark.anyio
@pytest.mark.parametrize("status", [401, 403, 404])
async def test_a_refused_or_missing_file_is_not_publicly_accessible(status: int) -> None:
    with pytest.raises(NotPubliclyAccessibleError):
        await _fetch(lambda request: httpx.Response(status))


@pytest.mark.anyio
async def test_a_web_page_instead_of_the_file_is_not_publicly_accessible() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, headers={"content-type": "text/html; charset=utf-8"}, content=b"<html/>"
        )

    with pytest.raises(NotPubliclyAccessibleError):
        await _fetch(handler)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "location",
    [
        "https://example.org/file",
        "http://drive.google.com/file",
        "https://drive.google.com.example.org/file",
        "https://user@drive.google.com/file",
        "https://drive.google.com:8443/file",
        "https://drive.google.com:99999/file",
        "https://169.254.169.254/latest/meta-data",
    ],
)
async def test_a_redirect_out_of_google_drive_is_refused(location: str) -> None:
    contacted: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        contacted.append(str(request.url.host))
        return _redirect(location)

    with pytest.raises(DownloadFailedError) as raised:
        await _fetch(handler)
    assert raised.value.reason == "Google Drive redirected to an unexpected address"
    assert contacted == ["drive.usercontent.google.com"]


@pytest.mark.anyio
async def test_a_redirect_without_address_fails() -> None:
    with pytest.raises(DownloadFailedError):
        await _fetch(lambda request: httpx.Response(302))


@pytest.mark.anyio
async def test_too_many_redirects_fail() -> None:
    with pytest.raises(DownloadFailedError) as raised:
        await _fetch(lambda request: _redirect("https://drive.google.com/again"))
    assert raised.value.reason == "Google Drive redirected too many times"


@pytest.mark.anyio
async def test_a_server_error_fails() -> None:
    with pytest.raises(DownloadFailedError) as raised:
        await _fetch(lambda request: httpx.Response(503))
    assert "503" in raised.value.reason


@pytest.mark.anyio
async def test_a_declared_length_over_the_limit_is_refused_before_reading() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-length": str(LIMIT + 1)}, content=b"x")

    with pytest.raises(InvalidScoreSizeError):
        await _fetch(handler)


@pytest.mark.anyio
async def test_the_download_stops_as_soon_as_the_limit_is_exceeded() -> None:
    sent: list[int] = []

    async def chunks() -> AsyncIterator[bytes]:
        for index in range(100):
            sent.append(index)
            yield b"x" * 512

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=chunks())

    with pytest.raises(InvalidScoreSizeError):
        await _fetch(handler)
    assert len(sent) == 3


@pytest.mark.anyio
async def test_a_content_of_exactly_the_limit_is_accepted() -> None:
    fetched = await _fetch(lambda request: httpx.Response(200, content=_streamed(b"x" * LIMIT)))
    assert fetched.size == LIMIT


@pytest.mark.anyio
async def test_a_network_failure_fails() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("unreachable", request=request)

    with pytest.raises(DownloadFailedError) as raised:
        await _fetch(handler)
    assert raised.value.reason == "the connection to Google Drive failed"


@pytest.mark.anyio
async def test_a_timeout_fails() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(DownloadFailedError) as raised:
        await _fetch(handler)
    assert raised.value.reason == "Google Drive did not answer in time"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("content_disposition", "file_name"),
    [
        ('attachment; filename="../../secret/score.pdf"', "score.pdf"),
        ('attachment; filename="C:\\Users\\score.pdf"', "score.pdf"),
        ('attachment; filename="bad\x01name.pdf"', "badname.pdf"),
        ('attachment; filename="' + "a" * 300 + '.pdf"', "a" * 255),
        ('attachment; filename="  "', "Google Drive file"),
        ("attachment", "Google Drive file"),
    ],
)
async def test_the_file_name_from_google_is_only_a_name(
    content_disposition: str, file_name: str
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, headers={"content-disposition": content_disposition}, content=_streamed(b"content")
        )

    assert (await _fetch(handler)).original_name == file_name
