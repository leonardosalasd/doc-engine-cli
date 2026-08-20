"""Downloading the images a document links to.

Off by default: a build should not reach the network because a Markdown file
happens to link a picture. `--fetch-images` turns it on, and then every download
is bounded — only http and https, a short timeout, a size ceiling, and a check
that what came back is actually an image.
"""

from __future__ import annotations

import hashlib
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TIMEOUT_SECONDS = 10
MAX_BYTES = 16 * 1024 * 1024

_ALLOWED_SCHEMES = ("http", "https")
_EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
    "image/bmp": ".bmp",
    "image/tiff": ".tiff",
}


class DownloadError(Exception):
    """An image that could not be fetched."""


def fetch(url: str, into: Path) -> Path:
    """Download *url* into *into* and return the file, raising DownloadError."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise DownloadError(f"only http and https are fetched, not {parsed.scheme or 'that'}")

    request = urllib.request.Request(url, headers={"User-Agent": "doc-engine-cli"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            content_type = response.headers.get_content_type()
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > MAX_BYTES:
                raise DownloadError(f"image is larger than {MAX_BYTES // 1024 // 1024} MB")
            payload = response.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise DownloadError(f"server answered {exc.code}") from exc
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise DownloadError(str(getattr(exc, "reason", exc))) from exc

    if len(payload) > MAX_BYTES:
        raise DownloadError(f"image is larger than {MAX_BYTES // 1024 // 1024} MB")

    suffix = _EXTENSIONS.get(content_type) or _suffix_from(url)
    if suffix is None:
        raise DownloadError(f"that is not an image ({content_type})")

    into.mkdir(parents=True, exist_ok=True)
    target = into / (hashlib.sha256(url.encode()).hexdigest()[:16] + suffix)
    target.write_bytes(payload)
    return target


def _suffix_from(url: str) -> str | None:
    suffix = Path(urllib.parse.urlparse(url).path).suffix.lower()
    return suffix if suffix in set(_EXTENSIONS.values()) | {".jpeg", ".tif"} else None
