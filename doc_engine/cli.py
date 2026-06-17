import os
import re
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from doc_engine import __version__
from doc_engine.compiler import DEFAULT_TEMPLATE, available_templates, compile_pdf
from doc_engine.converter import convert, extract_title, strip_first_heading
from doc_engine.linter import has_errors, lint

console = Console()

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


def _normalize_accent(ctx: click.Context, param: click.Parameter, value: str | None) -> str | None:
    if value is None:
        return None
    key = value.strip().lower()
    if key in _NAMED_ACCENTS:
        return _NAMED_ACCENTS[key]
    if _HEX.match(key):
        hex_part = key.lstrip("#")
        if len(hex_part) == 3:
            hex_part = "".join(ch * 2 for ch in hex_part)
        return f"#{hex_part}"
    names = ", ".join(sorted(_NAMED_ACCENTS))
    raise click.BadParameter(f"use a hex value like #2563eb or a name ({names}).")


def _print_issues(issues: list, filename: str) -> None:
    for issue in issues:
        color = "red" if issue.severity == "error" else "yellow"
        console.print(f"  [{color}]{issue.format(filename)}[/{color}]")


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="doc-engine")
@click.pass_context
def cli(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument("input_file", required=False, type=click.Path(exists=False))
@click.option("-o", "--output", default=None, help="Output PDF file path.")
@click.option("-t", "--title", default=None, help="Document title override.")
@click.option("-a", "--author", default=None, help="Author name override.")
@click.option(
    "--template",
    default=DEFAULT_TEMPLATE,
    type=click.Choice(available_templates(), case_sensitive=False),
    help="Layout to render with.",
)
@click.option(
    "--accent",
    default=None,
    callback=_normalize_accent,
    help="Accent color as a hex value (#2563eb) or a name (blue, teal, rose...).",
)
@click.option("--bib", default=None, help="Path to a custom .bib file.")
@click.option("--no-branding", "no_branding", is_flag=True, help="Hide the doc-engine attribution in the PDF.")
@click.option("--dry-run", "dry_run", is_flag=True, help="Check the Markdown for errors without producing a PDF.")
@click.option("--open", "open_pdf", is_flag=True, help="Open the PDF after generation.")
def build(
    input_file: str | None,
    output: str | None,
    title: str | None,
    author: str | None,
    template: str,
    accent: str | None,
    bib: str | None,
    no_branding: bool,
    dry_run: bool,
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

    markdown_content = input_path.read_text(encoding="utf-8")

    issues = lint(markdown_content)
    if dry_run:
        if issues:
            _print_issues(issues, str(input_path))
            errors = sum(1 for i in issues if i.severity == "error")
            warnings = len(issues) - errors
            console.print(f"\n[dim]{errors} error(s), {warnings} warning(s).[/dim]")
            raise SystemExit(1 if errors else 0)
        console.print("[bold green]✓[/bold green] No issues found.")
        return

    if issues:
        _print_issues(issues, str(input_path))
        console.print()
        if has_errors(issues):
            console.print("[bold red]Aborted:[/bold red] fix the errors above, or run [cyan]--dry-run[/cyan] to recheck.")
            raise SystemExit(1)

    resolved_bib = None
    if bib:
        resolved_bib = Path(bib)
        if not resolved_bib.exists():
            console.print(f"[bold yellow]Warning:[/bold yellow] Bibliography file not found — {bib}")
            resolved_bib = None
    else:
        resolved_bib = _find_file(cwd, _BIB_CANDIDATES)
        if resolved_bib:
            console.print(f"  [dim]Auto-detected bib:[/dim] [cyan]{resolved_bib.name}[/cyan]")

    resolved_title = title or extract_title(markdown_content)
    resolved_author = author or _detect_git_user()
    resolved_output = output or f"{input_path.stem}_doc.pdf"

    console.print(f"  [dim]Title:[/dim]    [white]{resolved_title}[/white]")
    console.print(f"  [dim]Author:[/dim]   [white]{resolved_author}[/white]")
    console.print(f"  [dim]Template:[/dim] [white]{template}[/white]")
    console.print(f"  [dim]Output:[/dim]   [cyan]{resolved_output}[/cyan]")
    console.print()

    with console.status("[bold blue]Converting Markdown → Typst…[/bold blue]"):
        stripped = strip_first_heading(markdown_content)
        typst_body = convert(stripped)

    with console.status("[bold blue]Compiling PDF…[/bold blue]"):
        try:
            compile_pdf(
                typst_body=typst_body,
                title=resolved_title,
                author=resolved_author,
                output_path=resolved_output,
                bib_file=str(resolved_bib.resolve()) if resolved_bib else None,
                template=template,
                accent=accent,
                branding=not no_branding,
                version=__version__,
            )
        except Exception as exc:
            message = getattr(exc, "message", None) or str(exc)
            console.print(f"\n[bold red]Compilation failed:[/bold red] {message}")
            for hint in getattr(exc, "hints", []) or []:
                console.print(f"  [dim]hint: {hint}[/dim]")
            raise SystemExit(1)

    console.print(f"[bold green]✓[/bold green] Generated → [bold cyan]{resolved_output}[/bold cyan]")

    if open_pdf:
        _open_file(resolved_output)


@cli.command()
def info() -> None:
    """Show version, repository, and available templates."""
    templates = ", ".join(available_templates())
    body = (
        f"[bold white]doc-engine-cli[/bold white] [dim]v{__version__}[/dim]\n"
        "Zero-config Markdown → PDF documentation engine.\n\n"
        f"[dim]Repository:[/dim] [cyan]{REPO_URL}[/cyan]\n"
        f"[dim]Templates:[/dim]  {templates}\n\n"
        "[dim]Common usage[/dim]\n"
        "  doc-engine build\n"
        "  doc-engine build README.md --template modern --accent teal\n"
        "  doc-engine build --dry-run\n\n"
        "[dim]Run[/dim] [cyan]doc-engine --help[/cyan] [dim]for every command and flag.[/dim]"
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
