# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-FileContributor: bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""End-to-end tests of personal mode: a real process spoken to over stdio."""

import json
import subprocess
import sys
from base64 import b64decode, b64encode
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from my_beautiful_choir.views.packaged.packaged_view import packaged_views_directory
from tests import score_samples
from tests.integration.stdio_session import TIMEOUT_SECONDS, StdioSession, launch_environment

LAUNCHER = Path(__file__).with_name("personal_mode_launcher.py")
ABOUT_URI = "ui://my-beautiful-choir/about.html"
DELETION_URI = "ui://my-beautiful-choir/deletion.html"
VIEWS = ("about.html", "deletion.html", "repertoire.html", "work.html")


def _write_stub_views(directory: Path) -> None:
    for view in VIEWS:
        (directory / view).write_text(f"<p>{view.removesuffix('.html')}</p>", encoding="utf-8")


def _exchange_show_about(session: StdioSession) -> dict[str, Any]:
    """Handshake, list the tools, call show_about; return its result."""
    assert session.initialize()["serverInfo"]["name"] == "my-beautiful-choir"
    tools = {tool["name"]: tool for tool in session.request(2, "tools/list")["tools"]}
    assert tools["show_about"]["_meta"]["ui"]["resourceUri"] == ABOUT_URI
    call = session.request(3, "tools/call", {"name": "show_about", "arguments": {}})
    assert call["structuredContent"]["mode"] == "personal"
    assert call["content"][0]["text"].endswith(", personal mode.")
    return session.request(4, "resources/read", {"uri": ABOUT_URI})


@pytest.fixture
def launched(tmp_path: Path) -> Iterator[StdioSession]:
    """The real entry point, with stub views."""
    _write_stub_views(tmp_path)
    session = StdioSession([sys.executable, str(LAUNCHER), str(tmp_path)], tmp_path / "data")
    yield session
    session.kill()


def test_personal_mode_serves_show_about_over_stdio(launched: StdioSession) -> None:
    resource = _exchange_show_about(launched)
    assert resource["contents"][0]["text"] == "<p>about</p>"

    exit_code, stderr = launched.close()
    assert exit_code == 0, stderr
    assert launched.stdout_lines.empty()
    # logs go to stderr, as JSON
    messages = [json.loads(line)["message"] for line in stderr.splitlines() if line.startswith("{")]
    assert "Starting my-beautiful-choir" in messages
    assert "Data store ready" in messages


def _tool_result(
    session: StdioSession, request_id: int, tool: str, **arguments: object
) -> dict[str, Any]:
    result = session.request(request_id, "tools/call", {"name": tool, "arguments": arguments})
    assert not result.get("isError"), result
    return result


def _call(session: StdioSession, request_id: int, tool: str, **arguments: object) -> str:
    return str(_tool_result(session, request_id, tool, **arguments)["content"][0]["text"])


def test_finalises_draft_after_review_over_stdio(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MBC_SCORE_LIFECYCLE__TRUSTED_FINALISATION_HOST", "true")
    _write_stub_views(tmp_path)
    session = StdioSession([sys.executable, str(LAUNCHER), str(tmp_path)], tmp_path / "data")
    try:
        session.initialize()
        _call(session, 2, "create_choir", name="Choir")
        work = _tool_result(session, 3, "add_work", title="Song")["structuredContent"]["work"]
        draft = _tool_result(
            session, 4, "add_musicxml_score", work_id=work["id"], xml=score_samples.musicxml_text()
        )["structuredContent"]["score"]
        assert draft["state"] == "draft"
        download = _tool_result(session, 5, "get_score_file", score_id=draft["id"])
        assert download["content"][1]["resource"]["uri"].endswith("%20-%20DRAFT.musicxml")
        preview = _tool_result(session, 6, "preview_score_finalisation", score_id=draft["id"])
        token = preview["_meta"]["finalisation_token"]
        assert token not in str(preview["structuredContent"])
        final = _tool_result(session, 7, "confirm_score_finalisation", token=token)
        assert final["structuredContent"]["score"]["state"] == "final"
        assert final["structuredContent"]["score"]["version_number"] == 1
        replay = _tool_result(session, 8, "confirm_score_finalisation", token=token)
        assert replay["structuredContent"] == {"finalisation_stale": True}
        assert session.close()[0] == 0
    finally:
        session.kill()


def test_choirs_are_kept_in_the_data_directory(tmp_path: Path) -> None:
    _write_stub_views(tmp_path)
    command = [sys.executable, str(LAUNCHER), str(tmp_path)]
    first = StdioSession(command, tmp_path / "data")
    try:
        first.initialize()
        assert _call(first, 2, "create_choir", name="Chœur de Lyon").endswith("default choir.")
        assert first.close()[0] == 0
    finally:
        first.kill()
    second = StdioSession(command, tmp_path / "data")
    try:
        second.initialize()
        assert _call(second, 2, "list_choirs") == "1 choir(s): Chœur de Lyon (default)."
        assert second.close()[0] == 0
    finally:
        second.kill()
    assert (tmp_path / "data" / "my-beautiful-choir.sqlite3").is_file()


def test_missing_view_exits_with_4_without_writing_to_stdout(tmp_path: Path) -> None:
    completed = subprocess.run(  # noqa: S603
        [sys.executable, str(LAUNCHER), str(tmp_path)],
        input="",
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=TIMEOUT_SECONDS,
        env=launch_environment(tmp_path / "data"),
        check=False,
    )
    assert completed.returncode == 4
    assert completed.stdout == ""
    assert "[MBC-INSTALL]" in completed.stderr


@pytest.mark.skipif(
    not all(packaged_views_directory().joinpath(view).is_file() for view in VIEWS),
    reason="the user interface is not built (uv run nox -s ui)",
)
def test_module_serves_the_built_views_and_confirms_a_deletion(tmp_path: Path) -> None:
    session = StdioSession([sys.executable, "-m", "my_beautiful_choir"], tmp_path / "data")
    try:
        resource = _exchange_show_about(session)
        [contents] = resource["contents"]
        assert contents["mimeType"] == "text/html;profile=mcp-app"
        assert contents["text"].startswith("<!doctype html>")
        assert "<script" in contents["text"]

        tools = {tool["name"]: tool for tool in session.request(5, "tools/list")["tools"]}
        assert tools["delete_choir"]["_meta"]["ui"]["resourceUri"] == DELETION_URI
        assert tools["confirm_deletion"]["_meta"]["ui"] == {
            "resourceUri": DELETION_URI,
            "visibility": ["app"],
        }
        deletion_resource = session.request(6, "resources/read", {"uri": DELETION_URI})
        [deletion_view] = deletion_resource["contents"]
        assert deletion_view["mimeType"] == "text/html;profile=mcp-app"
        assert deletion_view["text"].startswith("<!doctype html>")
        assert "<script" in deletion_view["text"]
        assert "<style" in deletion_view["text"]

        choir = "Chœur de Lyon"
        _call(session, 7, "create_choir", name=choir)
        requested = session.request(
            8, "tools/call", {"name": "delete_choir", "arguments": {"choir": choir}}
        )
        assert not requested.get("isError"), requested
        deletion = requested["structuredContent"]
        assert deletion["status"] == "pending"
        assert deletion["deletion"]["name"] == choir
        assert choir in _call(session, 9, "list_choirs")

        confirmation = {
            "name": "confirm_deletion",
            "arguments": {"token": deletion["token"]},
        }
        confirmed = session.request(10, "tools/call", confirmation)
        assert confirmed["structuredContent"]["status"] == "deleted"
        assert session.request(11, "tools/call", confirmation)["isError"]
        assert choir not in _call(session, 12, "list_choirs")
        _exercise_repertoire_views(session, tools)
        exit_code, stderr = session.close()
        assert exit_code == 0, stderr
    finally:
        session.kill()


def _exercise_repertoire_views(session: StdioSession, tools: dict[str, Any]) -> None:
    repertoire_uri = "ui://my-beautiful-choir/repertoire.html"
    work_uri = "ui://my-beautiful-choir/work.html"
    assert tools["show_repertoire"]["_meta"]["ui"]["resourceUri"] == repertoire_uri
    assert tools["show_work"]["_meta"]["ui"]["resourceUri"] == work_uri
    for name in (
        "upload_score",
        "download_score",
        "preview_score_deletion",
        "preview_work_deletion",
    ):
        assert tools[name]["_meta"]["ui"] == {"resourceUri": work_uri, "visibility": ["app"]}
    for index, uri in enumerate((repertoire_uri, work_uri), start=13):
        [view] = session.request(index, "resources/read", {"uri": uri})["contents"]
        assert view["mimeType"] == "text/html;profile=mcp-app"
        assert view["text"].startswith("<!doctype html>")
        assert "<script" in view["text"]
        assert "<style" in view["text"]

    _call(session, 15, "create_choir", name="Lyon")
    added = _tool_result(session, 16, "add_work", title="Étoile", composer="Boulanger")
    work_id = added["structuredContent"]["work"]["id"]
    uploaded = _tool_result(
        session,
        17,
        "upload_score",
        work_id=work_id,
        file_name="Alto.pdf",
        content=b64encode(score_samples.pdf()).decode(),
    )
    score_id = uploaded["structuredContent"]["score"]["id"]
    returned = _tool_result(session, 170, "get_score_file", score_id=score_id)
    [_, file] = returned["content"]
    assert file["type"] == "resource"
    assert file["resource"]["uri"] == "file:///Alto.pdf"
    assert file["resource"]["mimeType"] == "application/pdf"
    assert b64decode(file["resource"]["blob"]) == score_samples.pdf()
    downloaded = _tool_result(session, 171, "download_score", score_id=score_id)
    assert downloaded["content"][1]["resource"] == file["resource"]
    # No conversation limit, even for a client that declares no MCP Apps support.
    large_content = score_samples.pdf() + b"0" * 2 * 1024 * 1024
    large = _tool_result(
        session,
        172,
        "upload_score",
        work_id=work_id,
        file_name="Full.pdf",
        content=b64encode(large_content).decode(),
    )["structuredContent"]["score"]["id"]
    for request_id, tool in ((173, "download_score"), (174, "get_score_file")):
        [_, large_file] = _tool_result(session, request_id, tool, score_id=large)["content"]
        assert b64decode(large_file["resource"]["blob"]) == large_content
    deleted = _tool_result(session, 175, "preview_score_deletion", target_id=large)
    _tool_result(session, 176, "confirm_deletion", token=deleted["structuredContent"]["token"])
    repertoire = _tool_result(session, 18, "show_repertoire", search="etoile")["structuredContent"]
    assert repertoire["choir"] == "Lyon"
    [work_row] = repertoire["works"]
    assert (work_row["id"], work_row["score_count"]) == (work_id, 1)
    work = _tool_result(session, 19, "show_work", work_id=work_id)["structuredContent"]
    [score] = work["scores"]
    assert (score["id"], score["label"], score["format"]) == (score_id, "Alto", "pdf")
    score_preview = _tool_result(session, 20, "preview_score_deletion", target_id=score_id)
    _tool_result(session, 21, "confirm_deletion", token=score_preview["structuredContent"]["token"])
    shown = _tool_result(session, 22, "show_work", work_id=work_id)
    assert not shown["structuredContent"]["scores"]

    work_preview = _tool_result(session, 23, "preview_work_deletion", target_id=work_id)
    _tool_result(session, 24, "edit_work", work_id=work_id, title="Gloria")
    refreshed = _tool_result(
        session, 25, "confirm_deletion", token=work_preview["structuredContent"]["token"]
    )["structuredContent"]
    assert refreshed["status"] == "pending"
    assert refreshed["deletion"]["name"] == "Gloria"
    _tool_result(session, 26, "confirm_deletion", token=refreshed["token"])
    assert _tool_result(session, 27, "show_repertoire")["structuredContent"]["works"] == []


def test_find_and_send_scores_without_a_view(launched: StdioSession, tmp_path: Path) -> None:
    launched.initialize()
    tools = {tool["name"]: tool for tool in launched.request(2, "tools/list")["tools"]}
    for name in ("list_scores", "get_score_file"):
        assert "ui" not in tools[name].get("_meta", {})

    _call(launched, 3, "create_choir", name="Lyon")
    _call(launched, 4, "create_choir", name="Paris")
    works = [
        _tool_result(launched, index, "add_work", **work)["structuredContent"]["work"]["id"]
        for index, work in enumerate(
            (
                {"title": "Adeste fideles (NL15.2)"},
                {"title": "Peuple fidèle", "composer": "Composer A"},
                {"title": "Adeste fideles (NL15.20)"},
                {"title": "Other work", "composer": "NL15.2"},
                {"title": "Adeste fideles (NL15.2)", "choir": "Paris"},
            ),
            start=5,
        )
    ]

    for index, (work_id, selector, extension, content) in enumerate(
        (
            (works[0], {"work_reference": "nl15.2"}, "pdf", score_samples.pdf()),
            (works[1], {"work_title": "peuple fidele"}, "musicxml", score_samples.musicxml()),
        )
    ):
        path = tmp_path / f"Choir score.{extension}"
        path.write_bytes(content)
        added = _tool_result(
            launched, 10 + index * 3, "add_score_from_file", work_id=work_id, path=str(path)
        )["structuredContent"]["score"]
        found = _tool_result(launched, 11 + index * 3, "list_scores", **selector)[
            "structuredContent"
        ]
        assert found == {
            "work_id": work_id,
            "scores": [
                {
                    "id": added["id"],
                    "label": "Choir score",
                    "format": extension,
                    "state": "final",
                    "version_number": 1,
                }
            ],
        }
        files = _tool_result(launched, 12 + index * 3, "get_score_file", score_id=added["id"])
        assert b64decode(files["content"][1]["resource"]["blob"]) == content

    assert _tool_result(launched, 16, "list_scores", work_reference="NL15.2", choir="Paris")[
        "structuredContent"
    ] == {"work_id": works[4], "scores": []}
    assert _tool_result(launched, 17, "list_scores", work_id=works[2])["structuredContent"] == {
        "work_id": works[2],
        "scores": [],
    }
    _tool_result(launched, 18, "add_work", title="Peuple fidèle", composer="Composer B")
    ambiguous = _tool_result(launched, 19, "list_scores", work_title="Peuple fidèle")
    choices = ambiguous["structuredContent"]
    assert choices["work_count"] == 2
    assert "scores" not in choices
    assert [choice["label"] for choice in choices["works"]] == [
        "Peuple fidèle (Composer A)",
        "Peuple fidèle (Composer B)",
    ]
    assert all(choice["id"] in ambiguous["content"][0]["text"] for choice in choices["works"])
    missing = _tool_result(launched, 20, "list_scores", work_reference="NL15.3")
    assert missing["structuredContent"] == {"works": [], "work_count": 0}

    uri = tools["show_work"]["_meta"]["ui"]["resourceUri"]
    assert uri == "ui://my-beautiful-choir/work.html"
    shown = _tool_result(launched, 21, "show_work", work_id=works[0])
    assert shown["structuredContent"]["work"]["id"] == works[0]
    assert (
        launched.request(22, "resources/read", {"uri": uri})["contents"][0]["text"] == "<p>work</p>"
    )
