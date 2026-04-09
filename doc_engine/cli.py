import os
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from doc_engine import __version__
from doc_engine.compiler import compile_pdf
from doc_engine.converter import convert, extract_title, strip_first_heading

console = Console()

_README_CANDIDATES = ("README.md", "readme.md", "Readme.md", "README.MD")


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


def _find_readme(directory: Path) -> Path | None:
    for name in _README_CANDIDATES:
        candidate = directory / name
        if candidate.exists():
            return candidate
    return None


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
@click.option("--open", "open_pdf", is_flag=True, help="Open PDF after generation.")
def build(
    input_file: str | None,
    output: str | None,
    title: str | None,
    author: str | None,
    open_pdf: bool,
) -> None:
    console.print(
        Panel(
            f"[bold white]doc-engine[/bold white] [dim]v{__version__}[/dim]",
            border_style="blue",
            padding=(0, 2),
        )
    )

    if input_file:
        input_path = Path(input_file)
    else:
        input_path = _find_readme(Path.cwd())
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

    resolved_title = title or extract_title(markdown_content)
    resolved_author = author or _detect_git_user()
    resolved_output = output or f"{input_path.stem}_doc.pdf"

    console.print(f"  [dim]Title:[/dim]  [white]{resolved_title}[/white]")
    console.print(f"  [dim]Author:[/dim] [white]{resolved_author}[/white]")
    console.print(f"  [dim]Output:[/dim] [cyan]{resolved_output}[/cyan]")
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
            )
        except Exception as exc:
            console.print(f"\n[bold red]Compilation failed:[/bold red] {exc}")
            raise SystemExit(1)

    console.print(f"[bold green]✓[/bold green] Generated → [bold cyan]{resolved_output}[/bold cyan]")

    if open_pdf:
        _open_file(resolved_output)


def _open_file(path: str) -> None:
    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", path], check=False)
    else:
        subprocess.run(["xdg-open", path], check=False)


def main() -> None:
    cli()