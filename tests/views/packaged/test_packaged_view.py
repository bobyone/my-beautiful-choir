# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the packaged view."""

from pathlib import Path

import pytest

from my_beautiful_choir.views.errors import ViewNotFoundError
from my_beautiful_choir.views.packaged.packaged_view import PackagedView, packaged_views_directory


def test_uri_is_derived_from_the_name(tmp_path: Path) -> None:
    assert PackagedView("about", tmp_path).uri == "ui://my-beautiful-choir/about.html"


def test_content_is_read_once_then_kept(tmp_path: Path) -> None:
    document = tmp_path / "about.html"
    document.write_text("<p>À propos</p>", encoding="utf-8")
    view = PackagedView("about", tmp_path)
    assert view.content() == "<p>À propos</p>"
    document.write_text("<p>changed</p>", encoding="utf-8")
    assert view.content() == "<p>À propos</p>"


def test_missing_document_is_an_installation_error(tmp_path: Path) -> None:
    with pytest.raises(ViewNotFoundError) as raised:
        PackagedView("about", tmp_path).content()
    assert raised.value.uri == "ui://my-beautiful-choir/about.html"
    assert raised.value.exit_code == 4
    assert raised.value.error_code == "MBC-INSTALL"
    assert "nox -s ui" in raised.value.remedy


def test_packaged_directory_is_the_static_package() -> None:
    assert packaged_views_directory().joinpath("__init__.py").is_file()
