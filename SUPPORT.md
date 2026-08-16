# Getting Help

This project is maintained by one person in his spare time. Using the right
channel makes it much more likely your question gets a useful answer quickly.

---

## Where to go

| Your situation | Where |
|---|---|
| "How do I do X?" | [Discussions → Q&A](https://github.com/leonardosalasd/doc-engine-cli/discussions/categories/q-a) |
| "Something is broken" | [Issues](https://github.com/leonardosalasd/doc-engine-cli/issues) |
| "It would be great if it could..." | [Discussions → Ideas](https://github.com/leonardosalasd/doc-engine-cli/discussions/categories/ideas) |
| "I built something with it" | [Discussions → Show and tell](https://github.com/leonardosalasd/doc-engine-cli/discussions/categories/show-and-tell) |
| "I found a security problem" | [Security policy](SECURITY.md) — please report privately |
| "I want to contribute code" | [Contributing guide](CONTRIBUTING.md) |

The distinction that matters most: **questions go to Discussions, defects go to
Issues.** If you are not sure which one it is, open a discussion — it is easy to
convert it into an issue once we know a bug is involved.

---

## Before asking

Most questions are already answered:

- The [README](README.md) documents every command and flag, all five templates,
  front matter, watch mode, and custom templates.
- `doc-engine --help` and `doc-engine build --help` list every option.
- `doc-engine build --dry-run` checks a Markdown file for problems and reports
  them with the exact line and column.

---

## Writing a good question

Include enough for someone to reproduce what you are seeing:

- The exact command you ran.
- What you expected, and what happened instead.
- The full output or error message — the complete text, not a screenshot of a
  fragment.
- Your OS, your Python version, and the output of `doc-engine --version`.
- A minimal Markdown file that shows the problem, if the issue is with a
  particular document.

---

## Response times

There is no service level agreement here. Expect a reply within a few days;
security reports are handled first, then bugs that break normal usage, then
everything else.

If a thread goes quiet, a polite follow-up is fine — things fall through the
cracks sometimes.
