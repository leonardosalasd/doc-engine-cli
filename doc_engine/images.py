"""Placing pictures that are taller than a page.

A wide diagram only has to be scaled down. A tall one — a top-down flowchart,
a long schema — has no good answer at page width: scaled to fit a single page it
becomes unreadable, and left alone it runs off the bottom. Typst does not
paginate an image, so the picture is cut into page-sized pieces here and placed
one after another.
"""

from __future__ import annotations

import math
from pathlib import Path

# Height divided by width for each page size, used to decide when a picture is
# too tall to sit on one page. Every A and B size shares the same proportions.
_ISO_RATIO = math.sqrt(2)
PAGE_RATIOS = {
    "a3": _ISO_RATIO,
    "a4": _ISO_RATIO,
    "a5": _ISO_RATIO,
    "a6": _ISO_RATIO,
    "iso-b5": _ISO_RATIO,
    "jis-b5": _ISO_RATIO,
    "us-letter": 11 / 8.5,
    "us-legal": 14 / 8.5,
    "us-tabloid": 17 / 11,
}

# A picture is only cut when it is clearly taller than the page, so ordinary
# portrait figures are left alone.
TOLERANCE = 1.15

# Cutting a picture into more pieces than this means each one is a sliver.
MAX_PIECES = 12


class SplitError(Exception):
    """A picture that could not be cut."""


def page_ratio(paper: str) -> float:
    return PAGE_RATIOS.get(paper, _ISO_RATIO)


def needs_splitting(width: int, height: int, ratio: float) -> bool:
    return width > 0 and height / width > ratio * TOLERANCE


def split(source: Path, into: Path, ratio: float, stem: str) -> list[Path]:
    """Cut *source* into page-tall pieces, returning them in reading order."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise SplitError(
            "splitting tall images needs the 'pillow' package, which ships with "
            "doc-engine-cli — reinstall with 'pip install --upgrade doc-engine-cli'"
        ) from exc

    try:
        with Image.open(source) as picture:
            picture.load()
            width, height = picture.size
            if not needs_splitting(width, height, ratio):
                return [source]

            pieces = min(math.ceil((height / width) / ratio), MAX_PIECES)
            step = math.ceil(height / pieces)

            into.mkdir(parents=True, exist_ok=True)
            written: list[Path] = []
            for index in range(pieces):
                top = index * step
                bottom = min(top + step, height)
                if top >= bottom:
                    break
                target = into / f"{stem}_{index}.png"
                picture.crop((0, top, width, bottom)).save(target)
                written.append(target)
            return written
    except OSError as exc:
        raise SplitError(f"could not read {source.name}: {exc}") from exc
