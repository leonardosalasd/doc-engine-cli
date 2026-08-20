"""Project-level defaults from a `.doc-engine.toml` file.

A team that always builds with the same layout should not have to repeat the
flags, and should not have to put them in every document's front matter either:

    [doc-engine]
    template = "report"
    accent = "teal"
    paper = "us-letter"

Settings are read from `.doc-engine.toml` in the current folder, or from a
`[tool.doc-engine]` table in `pyproject.toml`. Front matter overrides the file,
and a command-line flag overrides both.
"""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # tomllib landed in 3.11; tomli is the same parser under its old name.
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

CONFIG_NAME = ".doc-engine.toml"
_PYPROJECT = "pyproject.toml"

# Only these keys mean anything; anything else in the table is ignored so a
# typo cannot silently change how a document is built.
KNOWN_KEYS = (
    "template",
    "accent",
    "paper",
    "author",
    "bib",
    "branding",
    "pdf_standard",
    "fetch_images",
)


class ConfigError(Exception):
    """A configuration file that could not be read."""


def load(directory: Path) -> dict[str, str]:
    """Return the settings for a build started in *directory*."""
    if tomllib is None:
        return {}

    dedicated = directory / CONFIG_NAME
    if dedicated.is_file():
        return _read(dedicated, ("doc-engine", "doc_engine"))

    pyproject = directory / _PYPROJECT
    if pyproject.is_file():
        return _read(pyproject, ("tool",), nested="doc-engine")

    return {}


def _read(path: Path, keys: tuple[str, ...], nested: str | None = None) -> dict[str, str]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError) as exc:
        raise ConfigError(f"{path.name}: {exc}") from exc

    table: dict = {}
    for key in keys:
        found = data.get(key)
        if isinstance(found, dict):
            table = found.get(nested, {}) if nested else found
            if isinstance(table, dict) and table:
                break
            table = {}

    return {
        key: _stringify(value)
        for key, value in table.items()
        if key in KNOWN_KEYS and value is not None
    }


def _stringify(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
