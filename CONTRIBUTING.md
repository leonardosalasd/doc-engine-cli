# Contributing to doc-engine-cli

Contributions are welcome from anyone — bug reports, documentation fixes, new
templates, and features are all useful. This guide covers what you need to know
to get a change merged.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Ways to contribute

| I want to... | Go here |
|---|---|
| Report a bug | [Open an issue](https://github.com/leonardosalasd/doc-engine-cli/issues/new) |
| Ask a question | [Discussions → Q&A](https://github.com/leonardosalasd/doc-engine-cli/discussions/categories/q-a) |
| Suggest a feature | [Discussions → Ideas](https://github.com/leonardosalasd/doc-engine-cli/discussions/categories/ideas) |
| Report a security issue | [Security policy](SECURITY.md) — please do not open a public issue |
| Fix something yourself | Read on |

---

## Getting set up

```bash
git clone https://github.com/leonardosalasd/doc-engine-cli.git
cd doc-engine-cli
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Check that the tool runs before changing anything:

```bash
doc-engine info
python -m pytest tests/ -v
```

---

## Testing

Run the suite before opening a pull request:

```bash
python -m pytest tests/ -v
```

**Test on more than one Python version.** This matters more than it sounds:
`v1.1.0` shipped completely broken on Python 3.10 through 3.13 because it was
only ever run on 3.14, where deferred annotation evaluation hid an import-time
crash. CI now covers 3.10–3.14 on Linux, macOS, and Windows, but catching it
locally is faster. If you have [uv](https://github.com/astral-sh/uv):

```bash
uv run --python 3.10 --no-project --with mistune --with click --with rich \
  --with typst --with pytest python -m pytest tests/ -q
```

Swap `3.10` for any version in the supported range.

New behavior needs a test. Bug fixes need a test that fails before the fix and
passes after it — that is what stops the same bug from coming back.

---

## Code style

Formatting and linting are handled by [ruff](https://docs.astral.sh/ruff/), and
CI checks both. Before opening a pull request:

```bash
ruff format doc_engine/ tests/
ruff check doc_engine/ tests/
```

Ruff settles the mechanical questions. The rest is convention — match the
surrounding code:

- Type hints on function signatures.
- Module-level constants in `SCREAMING_SNAKE_CASE`, prefixed with `_` when private.
- Helper functions prefixed with `_`.
- Tests grouped in classes named `TestSomething`, one behavior per method.
- Docstrings where the *why* is not obvious from the code. Skip them where it is.
- No decorative comment banners (`# ====`, `# ----`). If a comment is needed,
  write a sentence explaining the reasoning, not a divider.

Keep changes focused. A pull request that fixes one thing is easier to review,
and far easier to revert if it turns out to be wrong.

---

## Commit messages

The history uses [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add support for A4 page size
fix: prevent crash on legacy Windows consoles
docs: document the --watch flag
ci: test on Python 3.14
chore: bump version to 1.1.1
```

Write the subject in the imperative mood, under ~72 characters. If the change
needs explanation, put it in the body: what was broken, why the fix works, and
anything a future reader would need in order to not undo it by accident.

---

## Pull requests

1. Branch from `main` using a descriptive prefix: `feat/`, `fix/`, or `docs/`.
2. Make your change, with tests.
3. Run the suite and confirm it passes.
4. Open the pull request against `main`.

Every pull request is reviewed by the repository owner
([CODEOWNERS](.github/CODEOWNERS)), and CI must be green before merging. CI runs
the test suite across every supported Python version and operating system, plus
a smoke job that installs the built package and drives the CLI from a clean
directory.

In the description, explain what changed and why. If it fixes an open issue,
reference it with `Fixes #123`.

---

## Adding a template

Templates live in [`doc_engine/templates/`](doc_engine/templates) as `.typ`
files. Each one exposes a single `setup_doc` entry point, and the compiler
passes it the document metadata:

```typ
#let setup_doc(
  title: "",
  subtitle: "",
  author: "Anonymous",
  date: datetime.today().display(),
  bibliography_file: none,
  accent: none,
  branding: true,
  version: "",
  body,
) = { ... }
```

The quickest start is to copy an existing template and edit it. A new template
should:

- Honor `accent` when it is not `none`, and fall back to its own default color.
- Honor `branding: false` by hiding the `doc-engine` attribution.
- Render `subtitle` only when it is not empty.
- Render the bibliography when `bibliography_file` is not `none`.

Templates are discovered automatically, so dropping the file in is enough for
`--template <name>` to find it. Add it to the templates table in the README and
to the test in `tests/test_cli.py` that asserts the shipped set.

---

## Project layout

| Module | Responsibility |
|---|---|
| `cli.py` | Argument parsing, Git detection, watch loop, output naming |
| `frontmatter.py` | Leading `---` metadata block |
| `linter.py` | Source checks reported with line and column |
| `converter.py` | Markdown AST → Typst markup |
| `compiler.py` | Template injection and PDF compilation |

Changes usually belong in exactly one of these. If a change needs to touch all
of them, it is worth opening a discussion first to agree on the approach.

---

## Reporting bugs

A good report includes:

- What you ran and what happened, with the full error output.
- Your OS, Python version, and `doc-engine --version`.
- A minimal Markdown file that reproduces it, if the problem is in a document.

The report that led to `v1.1.1` was excellent precisely because it pasted the
entire traceback — that made the diagnosis immediate.

---

## License

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE) that covers this project.
