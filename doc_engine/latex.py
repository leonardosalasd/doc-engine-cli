"""LaTeX math translated into Typst math.

Typst has its own math language rather than a LaTeX dialect, so `$\\frac{a}{b}$`
means nothing to it: a backslash escapes the next character, and the compiler
ends up complaining about an unknown variable named `rac`. This module rewrites
the LaTeX people already have in their Markdown into the equivalent Typst.

Coverage is the common ground of real documents — Greek letters, operators and
relations, fractions and roots, sub- and superscripts, matrices, cases, and the
usual font commands. Anything unrecognized is passed through with its backslash
removed, which is usually right, since most LaTeX command names match a Typst
symbol of the same name.
"""

from __future__ import annotations

import re

# Every name here was checked against the Typst compiler; see tests/test_latex.py.
_SYMBOLS = {
    "varepsilon": "epsilon.alt",
    "vartheta": "theta.alt",
    "varphi": "phi.alt",
    "varrho": "rho.alt",
    "varsigma": "sigma.alt",
    "varpi": "pi.alt",
    "infty": "infinity",
    "cdot": "dot.op",
    "cdots": "dots.c",
    "ldots": "dots.h",
    "dots": "dots.h",
    "vdots": "dots.v",
    "ddots": "dots.down",
    "pm": "plus.minus",
    "mp": "minus.plus",
    "le": "<=",
    "leq": "<=",
    "ge": ">=",
    "geq": ">=",
    "ne": "!=",
    "neq": "!=",
    "ll": "<<",
    "gg": ">>",
    "sim": "tilde.op",
    "simeq": "tilde.eq",
    "cong": "tilde.equiv",
    "propto": "prop",
    "notin": "in.not",
    "ni": "in.rev",
    "subseteq": "subset.eq",
    "supseteq": "supset.eq",
    "cup": "union",
    "cap": "inter",
    "setminus": "without",
    "oplus": "xor",
    "otimes": "times.o",
    "circ": "compose",
    "to": "arrow.r",
    "rightarrow": "arrow.r",
    "leftarrow": "arrow.l",
    "leftrightarrow": "arrow.l.r",
    "Rightarrow": "arrow.r.double",
    "Leftarrow": "arrow.l.double",
    "Leftrightarrow": "arrow.l.r.double",
    "implies": "arrow.r.double",
    "iff": "arrow.l.r.double",
    "mapsto": "arrow.r.bar",
    "langle": "chevron.l",
    "rangle": "chevron.r",
    "mid": "|",
    "vert": "|",
    "Vert": "||",
    "lvert": "|",
    "rvert": "|",
    "lVert": "||",
    "rVert": "||",
    "emptyset": "emptyset",
    "varnothing": "emptyset",
    "prod": "product",
    "bigcup": "union.big",
    "bigcap": "inter.big",
    "int": "integral",
    "iint": "integral.double",
    "oint": "integral.cont",
    "nabla": "nabla",
    "partial": "partial",
    "ast": "ast",
    "star": "star",
    "bullet": "circle.filled.small",
    "top": "top",
    "bot": "bot",
    "perp": "perp",
    "angle": "angle",
    "triangle": "triangle",
    "aleph": "aleph",
    "hbar": "planck.reduce",
    "ell": "ell",
    "Re": "Re",
    "Im": "Im",
    "quad": "quad",
    "qquad": "wide",
}

# Commands whose LaTeX braces become Typst call arguments.
_ONE_ARG = {
    "sqrt": "sqrt",
    "text": None,
    "textrm": None,
    "textbf": "bold",
    "textit": "italic",
    "mathbb": "bb",
    "mathcal": "cal",
    "mathfrak": "frak",
    "mathbf": "bold",
    "mathit": "italic",
    "mathrm": "upright",
    "mathsf": "sans",
    "mathtt": "mono",
    "operatorname": None,
    "hat": "hat",
    "widehat": "hat",
    "bar": "macron",
    "overline": "overline",
    "underline": "underline",
    "vec": "arrow",
    "tilde": "tilde",
    "widetilde": "tilde",
    "dot": "dot",
    "ddot": "dot.double",
    "boldsymbol": "bold",
}

_TWO_ARG = {
    "frac": "frac",
    "dfrac": "frac",
    "tfrac": "frac",
    "binom": "binom",
}

# LaTeX environments and the Typst constructor that replaces them.
_MATRIX_ENVIRONMENTS = {
    "matrix": ("mat", None),
    "pmatrix": ("mat", "#none"),
    "bmatrix": ("mat", '"["'),
    "Bmatrix": ("mat", '"{"'),
    "vmatrix": ("mat", '"|"'),
    "Vmatrix": ("mat", '"||"'),
}

# How `\\` and `&` translate, per context: LaTeX separates matrix columns with
# `&` and rows with `\\`, while Typst uses `,` and `;`. In cases, every row is a
# single Typst argument, so `&` is only alignment and collapses to a space.
_ROW_SEPARATORS = {
    "normal": ("\\", "&"),
    "matrix": (";", ","),
    "cases": (",", " "),
}

_SPACING = {",": "thin", ";": "med", ":": "med", "!": "", " ": " "}
_COMMAND = re.compile(r"[A-Za-z]+")
_LETTERS = re.compile(r"[A-Za-z]+")

# Typst reads a run of letters as one identifier and fails when it does not know
# it, while LaTeX reads `xy` as x times y. Runs are therefore split into single
# letters unless they name one of these operators, which Typst does define.
_OPERATOR_NAMES = """
arccos arcsin arctan arg ceil cos cosh cot coth csc deg det dif dim exp floor
gcd hom id im inf ker lcm lim liminf limsup ln log max min mod Pr round sec
sin sinh sup tan tanh tr upright
"""
_OPERATORS = frozenset(_OPERATOR_NAMES.split())  # noqa: SIM905 - a word list reads better here


def to_typst(latex: str) -> str:
    """Translate a LaTeX math expression into Typst math markup."""
    return _convert(latex.strip()).strip()


def _convert(source: str, mode: str = "normal") -> str:
    out: list[str] = []
    index = 0
    while index < len(source):
        char = source[index]
        if char == "\\":
            text, index = _command(source, index, mode)
            _append(out, text)
        elif char == "{":
            group, index = _group(source, index)
            _append(out, f"({_convert(group, mode)})")
        elif char == "&":
            _append(out, _ROW_SEPARATORS[mode][1])
            index += 1
        elif char.isalpha():
            match = _LETTERS.match(source, index)
            run = match.group()
            index = match.end()
            _append(out, run if run in _OPERATORS else " ".join(run))
        else:
            _append(out, char)
            index += 1
    return "".join(out)


def _append(out: list[str], text: str) -> None:
    """Add *text*, keeping a space between neighbours that would otherwise merge.

    Typst would read the result of `i` followed by `\\pi` as one identifier
    called `ipi`, so adjacent names have to stay separated.
    """
    if text and out:
        previous = out[-1]
        if previous and (previous[-1].isalnum() or previous[-1] == ".") and text[0].isalnum():
            out.append(" ")
    out.append(text)


def _command(source: str, index: int, mode: str) -> tuple[str, int]:
    """Translate the command starting at the backslash in *index*."""
    index += 1
    if index >= len(source):
        return "", index

    char = source[index]
    if char == "\\":
        return _ROW_SEPARATORS[mode][0], index + 1
    if char in _SPACING:
        return _SPACING[char], index + 1
    if char in "{}|":
        return {"{": "{", "}": "}", "|": "||"}[char], index + 1

    match = _COMMAND.match(source, index)
    if not match:
        return char, index + 1

    name = match.group()
    index = match.end()

    if name == "begin":
        return _environment(source, index)
    if name == "end":
        _, index = _next_argument(source, index)
        return "", index
    if name in ("left", "right"):
        return "", index
    if name in _TWO_ARG:
        first, index = _next_argument(source, index)
        second, index = _next_argument(source, index)
        return f"{_TWO_ARG[name]}({_convert(first, mode)}, {_convert(second, mode)})", index
    if name in _ONE_ARG:
        if name == "sqrt" and _peek(source, index) == "[":
            degree, index = _bracket(source, index)
            radicand, index = _next_argument(source, index)
            return f"root({_convert(degree, mode)}, {_convert(radicand, mode)})", index
        argument, index = _next_argument(source, index)
        function = _ONE_ARG[name]
        if function is None:
            return f'"{argument.strip()}"', index
        return f"{function}({_convert(argument, mode)})", index

    return _SYMBOLS.get(name, name), index


def _environment(source: str, index: int) -> tuple[str, int]:
    """Translate a `\\begin{env}...\\end{env}` block into its Typst constructor."""
    name, index = _next_argument(source, index)
    name = name.strip()
    body, index = _environment_body(source, index, name)

    if name == "cases":
        return f"cases({_convert(body, 'cases').strip()})", index
    if name in _MATRIX_ENVIRONMENTS:
        constructor, delimiter = _MATRIX_ENVIRONMENTS[name]
        inner = _convert(body, "matrix").strip().strip(";").strip()
        if delimiter is None:
            return f"{constructor}(delim: #none, {inner})", index
        if delimiter == "#none":
            return f"{constructor}({inner})", index
        return f"{constructor}(delim: {delimiter}, {inner})", index
    return _convert(body, "normal"), index


def _environment_body(source: str, index: int, name: str) -> tuple[str, int]:
    """Return everything up to the matching `\\end{name}`, and the index past it."""
    closing = f"\\end{{{name}}}"
    end = source.find(closing, index)
    if end == -1:
        return source[index:], len(source)
    return source[index:end], end + len(closing)


def _next_argument(source: str, index: int) -> tuple[str, int]:
    """Read the next `{...}` group, or a single token when there are no braces."""
    while index < len(source) and source[index] == " ":
        index += 1
    if index >= len(source):
        return "", index
    if source[index] == "{":
        return _group(source, index)
    if source[index] == "\\":
        match = _COMMAND.match(source, index + 1)
        end = match.end() if match else index + 2
        return source[index:end], end
    return source[index], index + 1


def _group(source: str, index: int) -> tuple[str, int]:
    depth = 0
    start = index + 1
    while index < len(source):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start:index], index + 1
        index += 1
    return source[start:], index


def _bracket(source: str, index: int) -> tuple[str, int]:
    end = source.find("]", index)
    if end == -1:
        return "", index
    return source[index + 1 : end], end + 1


def _peek(source: str, index: int) -> str:
    return source[index] if index < len(source) else ""
