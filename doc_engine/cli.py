import os
import re
import subprocess
import sys
import time
from pathlib import Path

import click
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table

from doc_engine import __version__, frontmatter
from doc_engine.compiler import (
    DEFAULT_PAPER,
    DEFAULT_TEMPLATE,
    PAPER_SIZES,
    available_templates,
    compile_pdf,
)
from doc_engine.converter import convert_document, extract_title, strip_first_heading
from doc_engine.diagrams import DiagramError
from doc_engine.help import RichCommand, RichGroup
from doc_engine.linter import has_errors, lint

if sys.platform == "win32":
    # Legacy Windows consoles (cp1252 and similar) can't encode the arrows and
    # checkmarks below and crash on the first console.print(). Reconfiguring the
    # streams and skipping Rich's legacy renderer keeps output on every console.
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")

console = Console(legacy_windows=False) if sys.platform == "win32" else Console()

REPO_URL = "https://github.com/leonardosalasd/doc-engine-cli"

_README_CANDIDATES = ("README.md", "readme.md", "Readme.md", "README.MD")
_BIB_CANDIDATES = ("refs.bib", "references.bib", "bibliography.bib")

_NAMED_ACCENTS = {
    "blue": "#2563eb",
    "sky": "#0ea5e9",
    "indigo": "#4f46e5",
    "violet": "#7c3aed",
    "purple": "#9333ea",
    "red": "#dc2626",
    "rose": "#e11d48",
    "orange": "#ea580c",
    "amber": "#d97706",
    "green": "#16a34a",
    "emerald": "#059669",
    "teal": "#0d9488",
    "slate": "#475569",
    "black": "#111827",
}

_HEX = re.compile(r"^#?(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def _detect_git_user() -> str:
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        name = result.stdout.strip()
        return name if name else "Anonymous"
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return "Anonymous"


def _find_file(directory: Path, candidates: tuple[str, ...]) -> Path | None:
    for name in candidates:
        candidate = directory / name
        if candidate.exists():
            return candidate
    return None


def _accent_hex(value: str) -> str | None:
    key = value.strip().lower()
    if key in _NAMED_ACCENTS:
        return _NAMED_ACCENTS[key]
    if _HEX.match(key):
        hex_part = key.lstrip("#")
        if len(hex_part) == 3:
            hex_part = "".join(ch * 2 for ch in hex_part)
        return f"#{hex_part}"
    return None


def _normalize_accent(ctx: click.Context, param: click.Parameter, value: str | None) -> str | None:
    if value is None:
        return None
    accent = _accent_hex(value)
    if accent is None:
        names = ", ".join(sorted(_NAMED_ACCENTS))
        raise click.BadParameter(f"use a hex value like #2563eb or a name ({names}).")
    return accent


def _resolve_template(value: str) -> str | None:
    lowered = value.strip().lower()
    if lowered in available_templates():
        return lowered
    path = Path(value).expanduser()
    if path.suffix == ".typ" and path.is_file():
        return str(path)
    return None


def _template_callback(ctx: click.Context, param: click.Parameter, value: str | None) -> str | None:
    if value is None:
        return None
    resolved = _resolve_template(value)
    if resolved is None:
        choices = ", ".join(available_templates())
        raise click.BadParameter(f"pick one of ({choices}) or a path to a .typ file.")
    return resolved


def _resolve_paper(flag: str | None, from_meta: str | None) -> str | None:
    """Return the page size to use, or None when the front matter names an unknown one."""
    if flag:
        return flag.lower()
    if from_meta:
        key = from_meta.strip().lower()
        return key if key in PAPER_SIZES else None
    return DEFAULT_PAPER


def _template_label(template: str) -> str:
    return Path(template).stem if template.endswith(".typ") else template


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    index = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({index}){path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def _print_issues(issues: list, filename: str) -> None:
    for issue in issues:
        color = "red" if issue.severity == "error" else "yellow"
        console.print(f"  [{color}]{issue.format(filename)}[/{color}]")


@click.group(cls=RichGroup, invoke_without_command=True)
@click.version_option(__version__, prog_name="doc-engine")
@click.pass_context
def cli(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        ctx.get_help()


@cli.command(cls=RichCommand)
@click.argument("input_file", required=False, type=click.Path(exists=False))
@click.option("-o", "--output", default=None, help="Output PDF file path.")
@click.option("-t", "--title", default=None, help="Document title override.")
@click.option("-s", "--subtitle", default=None, help="Subtitle shown under the title.")
@click.option("-a", "--author", default=None, help="Author name override.")
@click.option("--date", default=None, help="Date shown on the cover.")
@click.option(
    "--template",
    default=None,
    callback=_template_callback,
    help="Built-in layout name or a path to a .typ template.",
)
@click.option(
    "--accent",
    default=None,
    callback=_normalize_accent,
    help="Accent color as a hex value (#2563eb) or a name (blue, teal, rose...).",
)
@click.option(
    "--paper",
    default=None,
    type=click.Choice(PAPER_SIZES, case_sensitive=False),
    help=f"Page size (default: {DEFAULT_PAPER}).",
)
@click.option("--bib", default=None, help="Path to a custom .bib file.")
@click.option("--no-branding", "no_branding", is_flag=True, help="Hide the doc-engine attribution in the PDF.")
@click.option("--dry-run", "dry_run", is_flag=True, help="Check the Markdown for errors without producing a PDF.")
@click.option("-w", "--watch", "watch", is_flag=True, help="Rebuild automatically whenever the source changes.")
@click.option("-f", "--force", "force", is_flag=True, help="Overwrite the output file instead of writing a new one.")
@click.option("--open", "open_pdf", is_flag=True, help="Open the PDF after generation.")
def build(
    input_file: str | None,
    output: str | None,
    title: str | None,
    subtitle: str | None,
    author: str | None,
    date: str | None,
    template: str | None,
    accent: str | None,
    paper: str | None,
    bib: str | None,
    no_branding: bool,
    dry_run: bool,
    watch: bool,
    force: bool,
    open_pdf: bool,
) -> None:
    """Convert a Markdown file into a professional PDF document."""
    console.print(
        Panel(
            f"[bold white]doc-engine[/bold white] [dim]v{__version__}[/dim]",
            border_style="blue",
            padding=(0, 2),
        )
    )

    cwd = Path.cwd()

    if input_file:
        input_path = Path(input_file)
    else:
        input_path = _find_file(cwd, _README_CANDIDATES)
        if not input_path:
            console.print(
                "[bold red]Error:[/bold red] No README.md found in current directory.\n"
                "[dim]Provide an input file or run from a directory containing a README.md.[/dim]"
            )
            raise SystemExit(1)
        console.print(f"  [dim]Auto-detected:[/dim] [cyan]{input_path.name}[/cyan]")

    if not input_path.exists():
        console.print(f"[bold red]Error:[/bold red] File not found — {input_path}")
        raise SystemExit(1)

    if dry_run:
        issues = lint(input_path.read_text(encoding="utf-8"))
        if issues:
            _print_issues(issues, str(input_path))
            errors = sum(1 for i in issues if i.severity == "error")
            console.print(f"\n[dim]{errors} error(s), {len(issues) - errors} warning(s).[/dim]")
            raise SystemExit(1 if errors else 0)
        console.print("[bold green]✓[/bold green] No issues found.")
        return

    output_path = Path(output) if output else Path(f"{input_path.stem}_doc.pdf")
    if not force:
        output_path = _unique_path(output_path)

    def run() -> bool:
        raw = input_path.read_text(encoding="utf-8")
        meta, content = frontmatter.parse(raw)

        issues = lint(raw)
        if issues:
            _print_issues(issues, str(input_path))
            console.print()
            if has_errors(issues):
                console.print("[bold red]Aborted:[/bold red] fix the errors above, or run [cyan]--dry-run[/cyan] to recheck.")
                return False

        resolved_template = template or _resolve_template(meta.get("template", DEFAULT_TEMPLATE))
        if resolved_template is None:
            console.print(f"[bold red]Error:[/bold red] Unknown template in front matter — {meta.get('template')}")
            return False

        resolved_accent = accent
        if resolved_accent is None and meta.get("accent"):
            resolved_accent = _accent_hex(meta["accent"])
            if resolved_accent is None:
                console.print(f"[bold yellow]Warning:[/bold yellow] Ignoring unknown accent — {meta['accent']}")

        resolved_bib = _resolve_bib(bib or meta.get("bib"), cwd)
        resolved_title = title or meta.get("title") or extract_title(content)
        resolved_author = author or meta.get("author") or _detect_git_user()
        resolved_subtitle = subtitle or meta.get("subtitle") or ""
        resolved_date = date or meta.get("date")
        resolved_paper = _resolve_paper(paper, meta.get("paper"))
        if resolved_paper is None:
            console.print(f"[bold red]Error:[/bold red] Unknown paper size — {meta.get('paper')}")
            return False

        console.print(f"  [dim]Title:[/dim]    [white]{resolved_title}[/white]")
        console.print(f"  [dim]Author:[/dim]   [white]{resolved_author}[/white]")
        console.print(
            f"  [dim]Template:[/dim] [white]{_template_label(resolved_template)}[/white]"
            f" [dim]on[/dim] [white]{resolved_paper}[/white]"
        )
        console.print(f"  [dim]Output:[/dim]   [cyan]{output_path}[/cyan]")
        console.print()

        with console.status("[bold blue]Converting Markdown → Typst…[/bold blue]"):
            try:
                conversion = convert_document(strip_first_heading(content), base_dir=input_path.parent)
            except DiagramError as exc:
                console.print(
                    f"\n[bold red]Diagram failed:[/bold red] {exc.language} block — {exc.message}"
                )
                return False

        with console.status("[bold blue]Compiling PDF…[/bold blue]"):
            try:
                compile_pdf(
                    typst_body=conversion.body,
                    title=resolved_title,
                    author=resolved_author,
                    subtitle=resolved_subtitle,
                    date=resolved_date,
                    output_path=str(output_path),
                    bib_file=str(resolved_bib.resolve()) if resolved_bib else None,
                    template=resolved_template,
                    accent=resolved_accent,
                    branding=not no_branding,
                    version=__version__,
                    assets=conversion.assets,
                    generated=conversion.generated,
                    paper=resolved_paper,
                )
            except Exception as exc:
                message = getattr(exc, "message", None) or str(exc)
                console.print(f"\n[bold red]Compilation failed:[/bold red] {message}")
                for hint in getattr(exc, "hints", []) or []:
                    console.print(f"  [dim]hint: {hint}[/dim]")
                return False

        console.print(f"[bold green]✓[/bold green] Generated → [bold cyan]{output_path}[/bold cyan]")
        return True

    ok = run()

    if open_pdf and ok:
        _open_file(str(output_path))

    if watch:
        _watch(input_path, run)
    elif not ok:
        raise SystemExit(1)


def _resolve_bib(bib: str | None, cwd: Path) -> Path | None:
    if bib:
        path = Path(bib)
        if path.exists():
            return path
        console.print(f"[bold yellow]Warning:[/bold yellow] Bibliography file not found — {bib}")
        return None
    found = _find_file(cwd, _BIB_CANDIDATES)
    if found:
        console.print(f"  [dim]Auto-detected bib:[/dim] [cyan]{found.name}[/cyan]")
    return found


def _watch(input_path: Path, run) -> None:
    console.print("\n[dim]Watching for changes — press Ctrl+C to stop.[/dim]")
    last = _mtime(input_path)
    try:
        while True:
            time.sleep(0.5)
            current = _mtime(input_path)
            if current != last:
                last = current
                console.rule(f"[dim]{time.strftime('%H:%M:%S')} — rebuilding[/dim]")
                run()
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped.[/dim]")


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


@cli.command(cls=RichCommand)
def info() -> None:
    """Show version, repository, and what this build supports."""
    facts = Table.grid(padding=(0, 2))
    facts.add_column(style="dim", no_wrap=True, vertical="top")
    facts.add_column()
    facts.add_row("Repository", f"[cyan]{REPO_URL}[/cyan]")
    facts.add_row("Templates", ", ".join(available_templates()))
    facts.add_row("Page sizes", f"{', '.join(PAPER_SIZES)} [dim](default {DEFAULT_PAPER})[/dim]")
    facts.add_row("Accents", f"{', '.join(sorted(_NAMED_ACCENTS))} [dim]or any hex[/dim]")

    body = Group(
        f"[bold white]doc-engine-cli[/bold white] [dim]v{__version__}[/dim]",
        "Turn Markdown into a polished PDF. No LaTeX, no config.",
        "",
        facts,
        "",
        "[dim]Markdown support[/dim]",
        "  tables · task lists · footnotes · local images · bibliography",
        "  mermaid and svg code blocks rendered as diagrams",
        "  LaTeX math, inline with $…$ and display with $$…$$",
        "",
        "[dim]Run[/dim] [cyan]doc-engine --help[/cyan] [dim]for every command and flag.[/dim]",
    )
    console.print(Panel(body, border_style="blue", padding=(1, 2), title="info"))


def _open_file(path: str) -> None:
    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", path], check=False)
    else:
        subprocess.run(["xdg-open", path], check=False)


def main() -> None:
    cli()
