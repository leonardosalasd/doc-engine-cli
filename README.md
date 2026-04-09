<div align="center">

# doc-engine-cli

**Zero-config Markdown → PDF documentation engine**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/badge/PyPI-v0.1.0-006DAD.svg?logo=pypi&logoColor=white)](https://pypi.org/project/doc-engine-cli/)
[![Typst](https://img.shields.io/badge/Powered_by-Typst-239DAD.svg?logo=typst&logoColor=white)](https://typst.app/)
[![Code style: black](https://img.shields.io/badge/code_style-black-000000.svg)](https://github.com/psf/black)

Transform any `README.md` into a premium, print-ready PDF report — no configuration, no templates, no LaTeX.

```
pip install doc-engine-cli
```

---

</div>

## Overview

**doc-engine-cli** is a developer-first CLI tool that converts Markdown files into professionally styled PDF documents using [Typst](https://typst.app/) as its rendering backend. It is designed for teams and individual developers who need high-quality documentation artifacts without the complexity of LaTeX or manual typesetting.

The tool auto-detects your `README.md`, extracts metadata from Git, and produces an IEEE-inspired technical document — complete with cover page, table of contents, and premium typography — in a single command.

```bash
doc-engine build
```

That's it. Zero configuration required.

---

## Features

| Feature | Description |
|---|---|
| **Zero-Config** | Auto-detects `README.md`, Git author, and document title. No setup files needed. |
| **Premium Typography** | Inter font family with fallback chain, justified text, and optimized line spacing. |
| **Code-Centric** | Syntax-highlighted code blocks with Cascadia Code font and GitHub-style backgrounds. |
| **Academic Ready** | IEEE and white paper-inspired layout with cover page and table of contents. |
| **Pure Python** | No external binaries required (no Pandoc, no LaTeX). Ships as a single `pip install`. |
| **Cross-Platform** | Works on Windows, macOS, and Linux with Python 3.10+. |

---

## Quick Start

### Installation

```bash
pip install doc-engine-cli
```

### Generate Your First PDF

Navigate to any project directory containing a `README.md` and run:

```bash
doc-engine build
```

The tool will:

1. Auto-detect `README.md` in the current directory
2. Extract the document title from the first `# heading`
3. Read your Git `user.name` for the author field
4. Generate a `README_doc.pdf` with cover page, ToC, and formatted content

### Explicit Options

```bash
doc-engine build path/to/file.md -o output.pdf -t "Custom Title" -a "Author Name"
```

---

## Usage

### CLI Reference

```
Usage: doc-engine build [OPTIONS] [INPUT_FILE]

  Convert a Markdown file into a professional PDF document.

Arguments:
  INPUT_FILE    Path to Markdown file (default: auto-detect README.md)

Options:
  -o, --output  TEXT    Output PDF file path (default: <input>_doc.pdf)
  -t, --title   TEXT    Document title override (default: first # heading)
  -a, --author  TEXT    Author name override (default: git user.name)
  --open                Open PDF after generation
  --version             Show version and exit
  --help                Show this message and exit
```

### Examples

**Basic — zero-config mode:**
```bash
cd my-project
doc-engine build
# → Generates README_doc.pdf
```

**Specify input and output:**
```bash
doc-engine build CONTRIBUTING.md -o contributing_guide.pdf
```

**Override metadata:**
```bash
doc-engine build -t "API Reference v2.0" -a "Engineering Team"
```

**Generate and open immediately:**
```bash
doc-engine build --open
```

**Use as Python module:**
```bash
python -m doc_engine build README.md
```

---

## Architecture

```
                    ┌─────────────┐
                    │  README.md  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   CLI Layer  │  click + rich
                    │  (cli.py)    │  arg parsing, git detection
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │                         │
       ┌──────▼──────┐          ┌───────▼──────┐
       │  Converter   │          │   Compiler   │
       │(converter.py)│          │(compiler.py) │
       │              │          │              │
       │ Markdown AST │          │  Typst → PDF │
       │  → Typst     │          │  via typst-py│
       └──────┬──────┘          └───────┬──────┘
              │                         │
              │    ┌──────────────┐     │
              └────► report.typ   ◄─────┘
                   │  (template)  │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │  output.pdf  │
                   └─────────────┘
```

### Pipeline

| Stage | Module | Responsibility |
|---|---|---|
| **1. Input Resolution** | `cli.py` | Locate Markdown file, detect Git metadata |
| **2. Markdown Parsing** | `converter.py` | Parse Markdown AST via `mistune`, emit Typst markup |
| **3. Template Injection** | `compiler.py` | Merge converted content with `report.typ` template |
| **4. PDF Compilation** | `compiler.py` | Compile via `typst` Python bindings |

---

## How It Works

### Markdown → Typst Conversion

The converter module parses Markdown using [`mistune`](https://github.com/lepture/mistune) and generates equivalent Typst markup:

| Markdown | Typst Output |
|---|---|
| `# Heading` | `= Heading` |
| `**bold**` | `*bold*` |
| `*italic*` | `_italic_` |
| `` `code` `` | `` `code` `` |
| `[text](url)` | `#link("url")[text]` |
| `- item` | `- item` |
| `1. item` | `+ item` |
| `> blockquote` | `#block(...)` |
| `---` | `#line(...)` |

Special characters (`#`, `$`, `@`, `*`, `_`, etc.) are automatically escaped to prevent Typst interpretation.

### PDF Template

The included `report.typ` template provides:

- **Cover page** with title, author, and date
- **Table of contents** with depth-3 navigation
- **Running headers** with document title and author
- **Page footer** with page numbers and engine attribution
- **Code blocks** with rounded corners and subtle borders
- **Heading hierarchy** with accent-colored H2 sections

---

## Project Structure

```
doc-engine-cli/
├── doc_engine/
│   ├── __init__.py          # Package version
│   ├── __main__.py          # python -m doc_engine entrypoint
│   ├── cli.py               # Click-based CLI + Git detection
│   ├── converter.py         # Markdown → Typst transpiler
│   ├── compiler.py          # Typst → PDF compilation engine
│   └── templates/
│       └── report.typ       # Professional Typst report template
├── tests/
│   ├── __init__.py
│   └── test_converter.py    # Unit tests for converter module
├── pyproject.toml            # Package configuration + dependencies
├── LICENSE                   # MIT License
├── .gitignore
└── README.md
```

---

## Dependencies

| Package | Purpose | License |
|---|---|---|
| [`click`](https://click.palletsprojects.com/) | CLI framework | BSD-3 |
| [`rich`](https://github.com/Textualize/rich) | Terminal formatting and progress indicators | MIT |
| [`mistune`](https://github.com/lepture/mistune) | Markdown parser (pure Python) | BSD-3 |
| [`typst`](https://github.com/messense/typst-py) | Typst compiler bindings | Apache-2.0 |

All dependencies are pure Python — no external binaries (Pandoc, LaTeX, etc.) are required.

---

## Development

### Setup

```bash
git clone https://github.com/leonardosalasd/doc-engine-cli.git
cd doc-engine-cli
pip install -e ".[dev]"
```

### Run Tests

```bash
python -m pytest tests/ -v
```

### Project Commands

```bash
# Generate PDF from this project's README
python -m doc_engine build

# Run with verbose error output
python -m doc_engine build README.md -o docs_output.pdf
```

---

## Supported Markdown Elements

- [x] Headings (H1–H6)
- [x] Bold, italic, strikethrough
- [x] Inline code and fenced code blocks (with language hints)
- [x] Links
- [x] Ordered and unordered lists
- [x] Nested lists
- [x] Blockquotes
- [x] Tables
- [x] Horizontal rules
- [x] Line breaks (`<br>`)
- [ ] Images (rendered as alt-text; remote images not embedded)
- [ ] Footnotes
- [ ] Math blocks

---

## Roadmap

- [ ] Custom template injection via `--template` flag
- [ ] Multi-file documentation merge
- [ ] GitHub Actions integration for CI/CD pipelines
- [ ] Dark-mode PDF theme variant
- [ ] Image downloading and embedding for remote URLs
- [ ] YAML front-matter support for metadata override
- [ ] PDF/A compliance for archival

---

## Contributing

Contributions are welcome. Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`python -m pytest tests/ -v`)
5. Submit a pull request

---

## License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**Built with [Typst](https://typst.app/) · Parsed with [mistune](https://github.com/lepture/mistune) · Styled with [Rich](https://github.com/Textualize/rich)**

</div>