# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the Google Drive links."""

import pytest

from my_beautiful_choir.scores.sources.errors import ScoreSourceError, UnsupportedLinkError
from my_beautiful_choir.scores.sources.google_drive.google_drive_link import GoogleDriveLink

FILE_ID = "1aBcD_eFgH-ijKlMnOpQrStUvWxYz0123"


@pytest.mark.parametrize(
    "link",
    [
        f"https://drive.google.com/file/d/{FILE_ID}/view?usp=sharing",
        f"https://drive.google.com/file/d/{FILE_ID}/view",
        f"https://drive.google.com/file/d/{FILE_ID}/edit",
        f"https://drive.google.com/file/d/{FILE_ID}/preview",
        f"https://drive.google.com/file/d/{FILE_ID}",
        f"https://drive.google.com/file/d/{FILE_ID}/",
        f"https://drive.google.com/file/u/1/d/{FILE_ID}/view",
        f"https://drive.google.com/open?id={FILE_ID}",
        f"https://drive.google.com/uc?id={FILE_ID}&export=download",
        f"https://DRIVE.google.com:443/file/d/{FILE_ID}/view",
        f"  https://drive.google.com/file/d/{FILE_ID}/view  ",
    ],
)
def test_accepts_the_links_of_a_file(link: str) -> None:
    parsed = GoogleDriveLink.parse(link)
    assert parsed == GoogleDriveLink(file_id=FILE_ID)
    assert parsed.url == f"https://drive.google.com/file/d/{FILE_ID}/view"
    assert parsed.download_url == (
        f"https://drive.usercontent.google.com/download?id={FILE_ID}&export=download&confirm=t"
    )


def test_keeps_the_resource_key() -> None:
    parsed = GoogleDriveLink.parse(
        f"https://drive.google.com/file/d/{FILE_ID}/view?resourcekey=0-AbCdEfGhIjKl"
    )
    assert parsed.resource_key == "0-AbCdEfGhIjKl"
    assert parsed.url.endswith("/view?resourcekey=0-AbCdEfGhIjKl")
    assert parsed.download_url.endswith("&confirm=t&resourcekey=0-AbCdEfGhIjKl")


@pytest.mark.parametrize(
    "link",
    [
        "",
        "not a link",
        f"http://drive.google.com/file/d/{FILE_ID}/view",
        f"https://drive.google.com.example.org/file/d/{FILE_ID}/view",
        f"https://example.org/file/d/{FILE_ID}/view",
        f"https://user:secret@drive.google.com/file/d/{FILE_ID}/view",
        f"https://drive.google.com:8443/file/d/{FILE_ID}/view",
        f"https://drive.google.com:99999/file/d/{FILE_ID}/view",
        f"https://drive.google.com/drive/folders/{FILE_ID}",
        f"https://docs.google.com/document/d/{FILE_ID}/edit",
        f"https://drive.usercontent.google.com/download?id={FILE_ID}",
        "https://drive.google.com/file/d/short/view",
        f"https://drive.google.com/file/d/{FILE_ID}/view/more",
        "https://drive.google.com/file/d/../../etc/view",
        "https://drive.google.com/open?id=bad id value",
        f"https://drive.google.com/open?id={FILE_ID}&id={FILE_ID}",
        "https://drive.google.com/open",
        f"https://drive.google.com/file/d/{FILE_ID}/view?resourcekey=bad key",
    ],
)
def test_refuses_other_links(link: str) -> None:
    with pytest.raises(UnsupportedLinkError) as raised:
        GoogleDriveLink.parse(link)
    assert raised.value.link == link
    assert isinstance(raised.value, ScoreSourceError)
