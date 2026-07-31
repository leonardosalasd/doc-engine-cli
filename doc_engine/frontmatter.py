"""Optional YAML-style front matter at the top of a Markdown file.

A leading block fenced by `---` lets a document carry its own metadata, so the
same file renders the same way no matter who runs it:

    ---
    title: Design Notes
    author: Jane Doe
    template: modern
    accent: teal
    ---

Only flat `key: value` pairs are supported — enough for document metadata,
without pulling in a YAML dependency. A leading block that carries no pairs is
left alone, so a document that simply opens with a `---` horizontal rule keeps
its content.
"""

_FENCE = "---"


def parse(text: str) -> tuple[dict[str, str], str]:
    """Split *text* into its front-matter mapping and the remaining body."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FENCE:
        return {}, text

    meta: dict[str, str] = {}
    for index in range(1, len(lines)):
        line = lines[index]
        if line.strip() == _FENCE:
            if not meta:
                break
            body = "\n".join(lines[index + 1 :])
            return meta, body.lstrip("\n")
        key, value = _split(line)
        if key:
            meta[key] = value

    return {}, text


def _split(line: str) -> tuple[str, str]:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or ":" not in stripped:
        return "", ""
    key, _, value = stripped.partition(":")
    return key.strip().lower(), _unquote(value.strip())


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value
