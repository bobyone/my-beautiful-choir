# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later

"""Single definition of the project checks, shared by the pre-commit hook and CI.

Every session runs its tools through ``uv run`` in the project environment, so
that local runs and CI runs use exactly the locked versions.
"""

import re
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

import nox

nox.options.default_venv_backend = "none"
nox.options.sessions = ["check"]

ALLOWED_LICENSES = ";".join(
    [
        "Apache",
        "BSD",
        "ISC",
        "LGPL",
        "MIT",
        "MPL",
        "PSF",
        "Python Software Foundation",
        "GPL-2.0-or-later",
        "GPL-3.0",
        "Unlicense",
    ]
)

SIGNED_OFF_BY = re.compile(r"^Signed-off-by: .+ <.+>$", re.MULTILINE)

PROJECT_DIRECTORY = Path(__file__).parent
UI_DIRECTORY = PROJECT_DIRECTORY / "ui"
VIEWS_PACKAGE = PROJECT_DIRECTORY / "src" / "my_beautiful_choir" / "views" / "static"
THIRD_PARTY_NOTICES = "THIRD-PARTY-LICENSES.md"
DOCKER_CHECK_IMAGE = "my-beautiful-choir:check"
DOCKER_HEALTH_TIMEOUT_SECONDS = 60


def _uv_run(session: nox.Session, *args: str) -> None:
    # No bytecode cache: `reuse lint` reports __pycache__ files found in directories
    # that Git does not track yet.
    session.run("uv", "run", "--frozen", *args, external=True, env={"PYTHONDONTWRITEBYTECODE": "1"})


@nox.session
def lint(session: nox.Session) -> None:
    """Check style and formatting without changing files."""
    _uv_run(session, "ruff", "check", ".")
    _uv_run(session, "ruff", "format", "--check", ".")


@nox.session(name="format")
def format_(session: nox.Session) -> None:
    """Format files and apply automatic lint fixes."""
    _uv_run(session, "ruff", "format", ".")
    _uv_run(session, "ruff", "check", "--fix", ".")


@nox.session
def typecheck(session: nox.Session) -> None:
    """Check static types."""
    _uv_run(session, "--extra", "personal-ocr", "mypy")


@nox.session
def tests(session: nox.Session) -> None:
    """Run the tests and enforce the coverage threshold."""
    _uv_run(
        session,
        "--extra",
        "personal-ocr",
        "pytest",
        "--cov",
        "--cov-report=term",
        "--cov-report=xml",
        *session.posargs,
    )


@nox.session
def reuse(session: nox.Session) -> None:
    """Check REUSE compliance (licence and copyright of every file)."""
    _uv_run(session, "reuse", "lint")


@nox.session
def audit(session: nox.Session) -> None:
    """Audit locked dependencies for known vulnerabilities."""
    requirements = session.run(
        "uv",
        "export",
        "--frozen",
        "--format",
        "requirements-txt",
        "--no-emit-project",
        "--extra",
        "personal-ocr",
        external=True,
        silent=True,
    )
    if not isinstance(requirements, str):
        session.error("Could not export the locked requirements.")
    path = Path(session.create_tmp()) / "requirements.txt"
    path.write_text(requirements, encoding="utf-8")
    _uv_run(session, "pip-audit", "--strict", "--disable-pip", "--requirement", str(path))


@nox.session
def licenses(session: nox.Session) -> None:
    """Check that runtime dependencies have licences compatible with GPL-2.0-or-later."""
    session.run(
        "uv",
        "run",
        "--frozen",
        "--isolated",
        "--no-dev",
        "--extra",
        "personal-ocr",
        "--with",
        "pip-licenses",
        "pip-licenses",
        "--partial-match",
        f"--allow-only={ALLOWED_LICENSES}",
        "--ignore-packages",
        "my-beautiful-choir",
        "pip-licenses",
        "prettytable",
        "wcwidth",
        external=True,
    )


@nox.session
def dco(session: nox.Session) -> None:
    """Check that every commit of a range carries a Signed-off-by line.

    Usage: ``nox -s dco -- <base>..<head>``.
    """
    if not session.posargs:
        session.error("Give the commit range to check, e.g. nox -s dco -- origin/main..HEAD")
    revision_range = session.posargs[0]
    commits = subprocess.run(
        ["git", "rev-list", "--no-merges", revision_range],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.split()
    unsigned = []
    for commit in commits:
        message = subprocess.run(
            ["git", "log", "-1", "--format=%B", commit],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout
        if not SIGNED_OFF_BY.search(message):
            unsigned.append(commit)
    if unsigned:
        session.error(f"Commits without a Signed-off-by line: {', '.join(unsigned)}")
    session.log(f"{len(commits)} commit(s) checked, all signed off.")


@nox.session
def sign_off(session: nox.Session) -> None:
    """Check that a commit message file carries a Signed-off-by line (commit-msg hook)."""
    if not session.posargs:
        session.error("Give the commit message file to check.")
    message = Path(session.posargs[0]).read_text(encoding="utf-8")
    if not SIGNED_OFF_BY.search(message):
        session.error("The commit message must carry a Signed-off-by line: use git commit -s.")


def _npm(session: nox.Session, *args: str) -> None:
    session.run("npm", *args, external=True)


def _install_ui_dependencies(session: nox.Session, force: bool) -> None:
    """Install the locked UI dependencies (always in CI, once locally)."""
    if force or not (UI_DIRECTORY / "node_modules").is_dir():
        _npm(session, "ci", "--no-fund", "--no-audit")


@nox.session
def ui(session: nox.Session) -> None:
    """Build the views and copy them, with their licence notices, into the Python package.

    Pass ``-- --fresh`` to reinstall the UI dependencies first.
    """
    with session.chdir(UI_DIRECTORY):
        _install_ui_dependencies(session, force="--fresh" in session.posargs)
        _npm(session, "run", "build")
    VIEWS_PACKAGE.mkdir(parents=True, exist_ok=True)
    for built in sorted((UI_DIRECTORY / "dist" / "views").glob("*.html")):
        shutil.copyfile(built, VIEWS_PACKAGE / built.name)
        session.log(f"Copied {built.name} into {VIEWS_PACKAGE}")
    shutil.copyfile(
        UI_DIRECTORY / "dist" / ".vite" / "license.md", VIEWS_PACKAGE / THIRD_PARTY_NOTICES
    )


@nox.session
def package(session: nox.Session) -> None:
    """Build the views, then the wheel and the sdist, and check that the views are packaged."""
    ui(session)
    dist = PROJECT_DIRECTORY / "dist"
    shutil.rmtree(dist, ignore_errors=True)
    session.run("uv", "build", "--out-dir", str(dist), external=True)
    [wheel] = dist.glob("*.whl")
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    expected = {
        f"my_beautiful_choir/views/static/{view.name}"
        for view in UI_DIRECTORY.joinpath("views").glob("*.html")
    }
    expected.add(f"my_beautiful_choir/views/static/{THIRD_PARTY_NOTICES}")
    missing = sorted(expected - names)
    if missing:
        session.error(f"Missing from {wheel.name}: {', '.join(missing)}")
    session.log(f"{wheel.name} contains the views and their licence notices.")


@nox.session
def docker_check(session: nox.Session) -> None:
    """Build the web mode image, start it and wait until its health check reports healthy."""
    session.run("docker", "build", "--tag", DOCKER_CHECK_IMAGE, ".", external=True)
    user = _docker_output(session, "image", "inspect", "--format", "{{.Config.User}}")
    if user != "10001":
        session.error(f"The image must run as the non-root user 10001, not {user!r}.")
    container = _docker_output(session, "run", "--detach")
    try:
        deadline = time.monotonic() + DOCKER_HEALTH_TIMEOUT_SECONDS
        status = "starting"
        while time.monotonic() < deadline:
            status = str(
                session.run(
                    "docker",
                    "inspect",
                    "--format",
                    "{{.State.Health.Status}}",
                    container,
                    external=True,
                    silent=True,
                )
            ).strip()
            if status != "starting":
                break
            time.sleep(1)
        if status != "healthy":
            session.run("docker", "logs", container, external=True)
            session.error(f"The container is {status}, not healthy.")
        session.log("The container is healthy.")
    finally:
        session.run("docker", "rm", "--force", container, external=True, silent=True)


def _docker_output(session: nox.Session, *args: str) -> str:
    output = session.run("docker", *args, DOCKER_CHECK_IMAGE, external=True, silent=True)
    return str(output).strip()


@nox.session
def ui_check(session: nox.Session) -> None:
    """Check the UI: lint and format, types, tests with coverage, catalogues.

    Pass ``-- --fresh`` to reinstall the UI dependencies first.
    """
    with session.chdir(UI_DIRECTORY):
        _install_ui_dependencies(session, force="--fresh" in session.posargs)
        _npm(session, "run", "lint")
        _npm(session, "run", "typecheck")
        _npm(session, "run", "test")
        _npm(session, "run", "check-locales")


@nox.session
def ui_audit(session: nox.Session) -> None:
    """Audit the UI dependencies and check the licences of the bundled ones."""
    with session.chdir(UI_DIRECTORY):
        _install_ui_dependencies(session, force="--fresh" in session.posargs)
        _npm(session, "audit")
        _npm(session, "run", "licenses")


@nox.session
def check(session: nox.Session) -> None:
    """Checks run by the pre-commit hook: lint, types, tests, REUSE, user interface."""
    lint(session)
    typecheck(session)
    tests(session)
    reuse(session)
    ui_check(session)
