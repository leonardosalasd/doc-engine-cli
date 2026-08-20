"""Help screens rendered with Rich.

Click's default help splits the tool in two: `--help` lists the commands, and
the flags people actually want live behind `build --help`. Since building is
what nearly every run does, the top-level screen shows those flags directly,
grouped by what they affect rather than in one flat column.

Help text is read from the Click parameters themselves, so there is one source
of truth for every description.
"""

from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Which build options belong under which heading, in the order they are shown.
_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Input and output", ("output", "force", "open_pdf")),
    ("Document details", ("title", "subtitle", "author", "date", "bib")),
    ("Appearance", ("template", "accent", "paper", "no_branding")),
    ("While you work", ("watch", "dry_run")),
)

_EXAMPLES = (
    ("doc-engine build", "Build README.md from the current folder"),
    ("doc-engine build notes.md", "Build a specific file"),
    ("doc-engine build --watch", "Rebuild every time you save"),
    ("doc-engine build --template modern --accent teal", "Pick a layout and color"),
    ("doc-engine build --paper us-letter", "Use US Letter instead of A4"),
    ("doc-engine build --dry-run", "Check for problems without writing a PDF"),
)


class RichGroup(click.Group):
    """The top-level command, whose help doubles as the guide to `build`."""

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        console = Console()
        _banner(console, ctx)
        _usage(console)
        _examples(console)

        build = self.get_command(ctx, "build")
        if build is not None:
            _options(console, build)

        _commands(console, self, ctx)
        _footer(console)


class RichCommand(click.Command):
    """A subcommand whose options are grouped the same way."""

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        console = Console()
        console.print()
        console.print(
            Text.assemble(
                ("Usage  ", "bold"),
                (f"doc-engine {self.name} ", "bold cyan"),
                (_argument_hint(self), "cyan"),
                ("[OPTIONS]", "dim"),
            )
        )
        if self.help:
            console.print(Text(f"       {self.help.strip()}", style="dim"))
        if self.name == "build":
            _examples(console)
        _options(console, self)
        _footer(console)


def _banner(console: Console, ctx: click.Context) -> None:
    from doc_engine import __version__

    console.print()
    console.print(
        Panel(
            Text.assemble(
                ("doc-engine ", "bold white"),
                (f"v{__version__}", "dim"),
                ("\nTurn Markdown into a polished PDF. No LaTeX, no config.", "dim"),
            ),
            border_style="blue",
            padding=(0, 2),
        )
    )


def _usage(console: Console) -> None:
    console.print()
    console.print(
        Text.assemble(
            ("Usage  ", "bold"),
            ("doc-engine build ", "bold cyan"),
            ("[FILE] ", "cyan"),
            ("[OPTIONS]", "dim"),
        )
    )
    console.print(
        Text.assemble(
            ("       ", ""),
            ("FILE", "cyan"),
            (" defaults to the README.md in the current folder.", "dim"),
        )
    )


def _examples(console: Console) -> None:
    console.print()
    console.print(Text("Examples", style="bold"))
    table = Table.grid(padding=(0, 2))
    table.add_column(style="cyan", no_wrap=True)
    table.add_column(style="dim")
    for command, description in _EXAMPLES:
        table.add_row(f"  {command}", description)
    console.print(table)


def _options(console: Console, command: click.Command) -> None:
    by_name = {param.name: param for param in command.params}
    shown: set[str] = set()

    for heading, names in _GROUPS:
        rows = [(by_name[name], name) for name in names if name in by_name]
        if not rows:
            continue
        console.print()
        console.print(Text(heading, style="bold"))
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan", no_wrap=True)
        table.add_column()
        for param, name in rows:
            shown.add(name)
            table.add_row(f"  {_flags(param)}", _describe(param))
        console.print(table)

    extra = [
        param
        for param in command.params
        if param.name not in shown
        and isinstance(param, click.Option)
        and param.name not in ("help",)
    ]
    if extra:
        console.print()
        console.print(Text("Other", style="bold"))
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan", no_wrap=True)
        table.add_column()
        for param in extra:
            table.add_row(f"  {_flags(param)}", _describe(param))
        console.print(table)


def _commands(console: Console, group: click.Group, ctx: click.Context) -> None:
    console.print()
    console.print(Text("Commands", style="bold"))
    table = Table.grid(padding=(0, 2))
    table.add_column(style="cyan", no_wrap=True)
    table.add_column(style="dim")
    for name in sorted(group.list_commands(ctx)):
        command = group.get_command(ctx, name)
        if command is None:
            continue
        table.add_row(f"  doc-engine {name}", (command.short_help or command.help or "").strip())
    table.add_row("  doc-engine --version", "Print the version and exit")
    console.print(table)


def _footer(console: Console) -> None:
    console.print()
    console.print(
        Text.assemble(
            ("Docs  ", "dim"),
            ("https://github.com/leonardosalasd/doc-engine-cli", "cyan"),
        )
    )
    console.print()


def _flags(param: click.Parameter) -> str:
    if isinstance(param, click.Argument):
        return param.name.upper()
    return ", ".join(param.opts)


def _describe(param: click.Parameter) -> Text:
    text = Text(getattr(param, "help", "") or "")
    choices = param.type.choices if isinstance(param.type, click.Choice) else None
    if choices:
        text.append(f"\n{', '.join(choices)}", style="dim")
    return text


def _argument_hint(command: click.Command) -> str:
    names = [p.name.upper() for p in command.params if isinstance(p, click.Argument)]
    return f"[{names[0]}] " if names else ""
