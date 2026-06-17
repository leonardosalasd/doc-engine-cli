"""Source-level checks that run before the Typst compiler.

These catch the kind of mistakes that would otherwise blow up deep inside the
compiler with a position that points at generated Typst instead of the user's
Markdown. Every issue carries the real line and column in the source file.
"""

import re
from dataclasses import dataclass

_LINK = re.compile(r"(!?)\[(?P<text>[^\]]*)\]\((?P<url>[^)]*)\)")
_FENCE = re.compile(r"^\s*(```|~~~)")


@dataclass(frozen=True)
class Issue:
    line: int
    column: int
    severity: str
    message: str

    def format(self, filename: str) -> str:
        return f"{filename}:{self.line}:{self.column}: {self.severity}: {self.message}"


def lint(markdown: str) -> list[Issue]:
    """Return every problem found in the Markdown source, in reading order."""
    issues: list[Issue] = []
    lines = markdown.split("\n")

    in_fence = False
    fence_marker = ""
    fence_opened_at = 0

    for number, line in enumerate(lines, start=1):
        fence = _FENCE.match(line)
        if fence:
            marker = fence.group(1)
            if not in_fence:
                in_fence = True
                fence_marker = marker
                fence_opened_at = number
            elif marker == fence_marker:
                in_fence = False
            continue

        if in_fence:
            continue

        issues.extend(_check_links(line, number))

    if in_fence:
        issues.append(
            Issue(fence_opened_at, 1, "error", "unclosed fenced code block")
        )

    return issues


def _check_links(line: str, number: int) -> list[Issue]:
    found: list[Issue] = []
    for match in _LINK.finditer(line):
        is_image = match.group(1) == "!"
        url = match.group("url").strip()
        column = match.start() + 1
        if url:
            continue
        if is_image:
            found.append(
                Issue(number, column, "warning", "image source is empty")
            )
        else:
            found.append(
                Issue(number, column, "error", "link URL must not be empty")
            )
    return found


def has_errors(issues: list[Issue]) -> bool:
    return any(issue.severity == "error" for issue in issues)
