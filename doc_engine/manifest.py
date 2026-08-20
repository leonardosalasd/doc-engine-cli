"""A manifest that builds one PDF out of many files.

A project that outgrew a single Markdown file lists its parts in a manifest —
`doc-engine.md` by default — as ordinary Markdown links, so the file still reads
and renders as a table of contents on GitHub:

    ---
    title: Payments API
    template: academic
    ---

    - [Overview](doc/overview.md)
    - [Architecture](diagrams/architecture.mmd)
    - [Schema](img/schema.png)
    - [References](bib/references.bib)

Each entry is handled by what it is. Markdown files are appended as sections,
diagram sources are rendered where they appear, images are placed as figures,
and a bibliography is registered for the whole document. Paths resolve against
the manifest's own folder, and headings inside an included file keep their
levels, so a `##` stays a subsection of the entry above it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from doc_engine import diagrams, frontmatter
from doc_engine.converter import Conversion, convert_document

MANIFEST_NAMES = ("doc-engine.md", "docengine.md", "SUMMARY.md")

_LINK = re.compile(r"\[(?P<label>[^\]]*)\]\((?P<target>[^)]+)\)")

_MARKDOWN = {".md", ".markdown", ".mdown", ".mkd"}

# Only Mermaid needs rendering; Typst draws an .svg file directly, so those are
# copied like any other picture.
_DIAGRAM = {".mmd": "mermaid", ".mermaid": "mermaid"}
_IMAGE = {".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff"}
_BIBLIOGRAPHY = {".bib"}


class ManifestError(Exception):
    """A manifest that names something that cannot be used."""


@dataclass(frozen=True)
class Entry:
    kind: str
    label: str
    path: Path


@dataclass
class Manifest:
    metadata: dict[str, str]
    entries: list[Entry]
    bibliography: Path | None = None

    @property
    def sources(self) -> list[Path]:
        """Every file the build reads, for watch mode to follow."""
        return [entry.path for entry in self.entries]


def find(directory: Path) -> Path | None:
    for name in MANIFEST_NAMES:
        candidate = directory / name
        if candidate.is_file():
            return candidate
    return None


def is_manifest(path: Path) -> bool:
    return path.name in MANIFEST_NAMES


def load(path: Path) -> Manifest:
    """Read *path* and resolve every entry it names."""
    metadata, body = frontmatter.parse(path.read_text(encoding="utf-8"))
    base = path.parent

    entries: list[Entry] = []
    bibliography: Path | None = None
    missing: list[str] = []

    for match in _LINK.finditer(body):
        target = match.group("target").strip()
        if not target or _is_remote(target):
            continue

        resolved = (base / target).expanduser()
        if not resolved.is_file():
            missing.append(target)
            continue

        kind = _classify(resolved)
        if kind is None:
            continue
        if kind == "bibliography":
            bibliography = resolved
            continue
        entries.append(Entry(kind=kind, label=match.group("label").strip(), path=resolved))

    if missing:
        listed = ", ".join(missing)
        raise ManifestError(f"{path.name} points at files that do not exist: {listed}")
    if not entries:
        raise ManifestError(f"{path.name} lists no documents to build")

    return Manifest(metadata=metadata, entries=entries, bibliography=bibliography)


def assemble(
    manifest: Manifest,
    work_dir: Path | None = None,
    fetch_remote: bool = False,
    split_tall: float | None = None,
) -> Conversion:
    """Convert every entry and join the results into one document.

    Each entry is converted against its own folder, so a picture referenced from
    inside an included file resolves the way it does when that file is built on
    its own.
    """
    body: list[str] = []
    assets: dict[str, str] = {}
    generated: dict[str, str] = {}
    warnings: list[str] = []

    for position, entry in enumerate(manifest.entries):
        namespace = f"e{position}_"
        if entry.kind == "markdown":
            piece = convert_document(
                entry.path.read_text(encoding="utf-8"),
                base_dir=entry.path.parent,
                namespace=namespace,
                work_dir=work_dir,
                fetch_remote=fetch_remote,
                split_tall=split_tall,
            )
            body.append(piece.body)
            assets.update(piece.assets)
            generated.update(piece.generated)
            warnings.extend(piece.warnings)
        elif entry.kind == "diagram":
            name = f"assets/{namespace}{entry.path.stem}.svg"
            generated[name] = diagrams.render(
                diagram_language(entry.path), entry.path.read_text(encoding="utf-8")
            )
            body.append(_figure(name, entry.label))
        elif entry.kind == "image":
            name = f"assets/{namespace}{entry.path.name}"
            assets[name] = str(entry.path.resolve())
            body.append(_figure(name, entry.label))

    return Conversion(body="\n\n".join(body), assets=assets, generated=generated, warnings=warnings)


def _figure(name: str, label: str) -> str:
    picture = f'#align(center)[#fit-image("{name}")]'
    if not label:
        return picture
    caption = label.replace("\\", "\\\\").replace('"', '\\"')
    return f'#figure(fit-image("{name}"), caption: [{caption}])'


def _classify(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix in _MARKDOWN:
        return "markdown"
    if suffix in _DIAGRAM:
        return "diagram"
    if suffix in _IMAGE:
        return "image"
    if suffix in _BIBLIOGRAPHY:
        return "bibliography"
    return None


def diagram_language(path: Path) -> str:
    return _DIAGRAM[path.suffix.lower()]


def _is_remote(target: str) -> bool:
    return bool(re.match(r"^[a-z][a-z0-9+.-]*://", target, re.IGNORECASE)) or target.startswith("#")
