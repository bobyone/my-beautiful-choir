# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests of the settings loader."""

import pytest

from my_beautiful_choir.configuration.errors import ConfigurationError
from my_beautiful_choir.configuration.loader import load_settings
from my_beautiful_choir.configuration.mode import Mode


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "MBC_MODE",
        "MBC_LOG_LEVEL",
        "MBC_WEB__HOST",
        "MBC_WEB__PORT",
        "MBC_WEB__ALLOWED_HOSTS",
    ):
        monkeypatch.delenv(key, raising=False)


def test_defaults() -> None:
    settings = load_settings([])
    assert settings.mode is Mode.PERSONAL
    assert settings.log_level == "INFO"
    assert settings.web.host == "127.0.0.1"
    assert settings.web.port == 9000
    assert settings.web.allowed_hosts == ()


def test_environment_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MBC_MODE", "web")
    monkeypatch.setenv("MBC_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("MBC_WEB__HOST", "0.0.0.0")  # noqa: S104
    monkeypatch.setenv("MBC_WEB__PORT", "8080")
    monkeypatch.setenv("MBC_WEB__ALLOWED_HOSTS", "localhost:9000, choir.example.org ,")
    settings = load_settings([])
    assert settings.mode is Mode.WEB
    assert settings.log_level == "DEBUG"
    assert settings.web.host == "0.0.0.0"  # noqa: S104
    assert settings.web.port == 8080
    assert settings.web.allowed_hosts == ("localhost:9000", "choir.example.org")


def test_command_line_mode_takes_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MBC_MODE", "personal")
    assert load_settings(["--mode", "web"]).mode is Mode.WEB


def test_settings_are_immutable() -> None:
    settings = load_settings([])
    with pytest.raises(ValueError, match="frozen"):
        settings.mode = Mode.WEB


@pytest.mark.parametrize(
    ("variable", "value", "key"),
    [
        ("MBC_WEB__PORT", "90000", "MBC_WEB__PORT"),
        ("MBC_WEB__PORT", "abc", "MBC_WEB__PORT"),
        ("MBC_MODE", "cloud", "MBC_MODE"),
        ("MBC_LOG_LEVEL", "VERBOSE", "MBC_LOG_LEVEL"),
    ],
)
def test_invalid_environment_value(
    monkeypatch: pytest.MonkeyPatch, variable: str, value: str, key: str
) -> None:
    monkeypatch.setenv(variable, value)
    with pytest.raises(ConfigurationError) as raised:
        load_settings([])
    assert [issue.key for issue in raised.value.issues] == [key]
    assert repr(value) in raised.value.issues[0].message


def test_every_invalid_value_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MBC_WEB__PORT", "0")
    monkeypatch.setenv("MBC_LOG_LEVEL", "LOUD")
    with pytest.raises(ConfigurationError) as raised:
        load_settings([])
    assert {issue.key for issue in raised.value.issues} == {"MBC_WEB__PORT", "MBC_LOG_LEVEL"}


def test_invalid_command_line() -> None:
    with pytest.raises(ConfigurationError) as raised:
        load_settings(["--mode", "cloud"])
    assert raised.value.issues[0].key == "command line"
    assert raised.value.exit_code == 2
    assert raised.value.error_code == "MBC-CONFIG"


def test_version_option(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        load_settings(["--version"])
    assert raised.value.code == 0
    assert capsys.readouterr().out.startswith("my-beautiful-choir ")
