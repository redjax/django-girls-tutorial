import logging
from pathlib import Path
import platform
import importlib.util

import nox

log = logging.getLogger(__name__)

## Set nox options
if importlib.util.find_spec("uv"):
    nox.options.default_venv_backend = "uv|virtualenv"
else:
    nox.options.default_venv_backend = "virtualenv"
nox.options.reuse_existing_virtualenvs = True
nox.options.error_on_external_run = False
nox.options.error_on_missing_interpreters = False
# nox.options.report = True

## Define sessions to run when no session is specified
nox.sessions = ["lint", "export", "tests", "mysite"]

## Define versions to test
PY_VERSIONS: list[str] = ["3.12", "3.11"]
## Get tuple of Python ver ('maj', 'min', 'mic')
PY_VER_TUPLE: tuple[str, str, str] = platform.python_version_tuple()
## Dynamically set Python version
DEFAULT_PYTHON: str = f"{PY_VER_TUPLE[0]}.{PY_VER_TUPLE[1]}"

## Set PDM version to install throughout
PDM_VER: str = "2.15.4"
## Set paths to lint with the lint session
LINT_PATHS: list[str] = ["src", "tests"]


@nox.session(python=[DEFAULT_PYTHON], name="lint", tags=["quality"])
def run_linter(session: nox.Session):
    session.install("black")

    log.info("Linting code")
    for d in LINT_PATHS:
        if not Path(d).exists():
            log.warning(f"Skipping lint path '{d}', could not find path")
            pass
        else:
            lint_path: Path = Path(d)

            log.info(f"Formatting '{d}' with Black")
            session.run(
                "black",
                lint_path,
            )

    log.info("Linting noxfile.py")
    session.run("black", "noxfile.py")


@nox.session(python=[DEFAULT_PYTHON], name="export", tags=["requirements"])
@nox.parametrize("pdm_ver", [PDM_VER])
def export_requirements(session: nox.Session, pdm_ver: str):
    session.install(f"pdm>={pdm_ver}")

    log.info("Exporting production requirements")
    session.run(
        "pdm",
        "export",
        "--prod",
        "-o",
        "requirements.txt",
        "--without-hashes",
    )

    log.info("Exporting development requirements")
    session.run(
        "pdm",
        "export",
        "-d",
        "-o",
        "requirements.dev.txt",
        "--without-hashes",
    )


@nox.session(python=PY_VERSIONS, name="tests", tags=["test"])
@nox.parametrize("pdm_ver", [PDM_VER])
def run_tests(session: nox.Session, pdm_ver: str):
    session.install(f"pdm>={pdm_ver}")
    session.run("pdm", "install")

    log.info("Running Pytest tests")
    session.run(
        "pdm",
        "run",
        "pytest",
        "-n",
        "auto",
        "--tb=auto",
        "-v",
        "-rsXxfP",
    )


def _do_migration(session: nox.Session, app_name: str) -> bool:
    log.info(f"Making migration for '{app_name}'")
    try:
        session.run("python", "manage.py", "makemigrations", str(app_name))

    except Exception as exc:
        msg = f"({type(exc)}) Unhandled exception making migrations for '{app_name}'. Details: {exc}"
        log.error(msg)

        return False

    try:
        session.run("python", "manage.py", "migrate", str(app_name))
    except Exception as exc:
        msg = f"({type(exc)}) Unhandled exception while migrating '{app_name}'. Details: {exc}"
        log.error(msg)

        return False

    return True


@nox.session(python=DEFAULT_PYTHON, name="migrate", tags=["django", "db", "migration"])
def do_all_migrations(session: nox.Session):
    session.install("Django")

    log.info("Doing migrations")

    try:
        session.run("python", "manage.py", "makemigrations")
    except Exception as exc:
        msg = f"({type(exc)}) Unhandled exception making migrations. Details: {exc}"
        log.error(msg)

        return

    try:
        session.run("python", "manage.py", "migrate")
    except Exception as exc:
        msg = (
            f"({type(exc)}) Unhandled exception while migrating models. Details: {exc}"
        )
        log.error(msg)
