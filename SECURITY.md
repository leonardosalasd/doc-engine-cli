# Security Policy

## Supported versions

Security fixes are applied to the latest release. If you are on an older
version, upgrade before reporting:

```bash
pipx upgrade doc-engine-cli
```

| Version | Supported |
|---|---|
| 1.1.x | Yes |
| 1.0.x | Please upgrade |
| < 1.0 | No |

---

## Reporting a vulnerability

**Please do not open a public issue, discussion, or pull request for a security
problem.** Public reports expose users who have not upgraded yet.

Report it privately, in either of these ways:

1. **GitHub Security Advisories (preferred)** — use the
   [Security tab](https://github.com/leonardosalasd/doc-engine-cli/security)
   and choose *Report a vulnerability*. This opens a private advisory that only
   you and the maintainer can see, and it keeps the whole discussion, the fix,
   and the disclosure in one place.

2. **Email** — write to **leonardo.salas01@outlook.com**.

Sending both is welcome: the advisory keeps the technical thread organized, and
the email makes sure it is seen quickly.

### What to include

- The version of `doc-engine-cli` and your Python version and OS.
- What an attacker can achieve, and what access they would need to do it.
- Steps to reproduce, ideally with a minimal Markdown file, template, or
  command. Please describe the payload rather than attaching anything harmful.
- Any suggested fix, if you have one in mind.

### What to expect

- **Acknowledgement within 72 hours.** If you have not heard back by then,
  please send a follow-up — it means the message did not reach me.
- An assessment of whether the report is accepted, along with the reasoning.
- Progress updates while a fix is being prepared.
- A release with the fix, and a published advisory once users have had a
  reasonable chance to upgrade.

Please give me a chance to ship a fix before disclosing publicly. If you plan to
publish on a particular date, say so in your first message and we will work
toward it.

---

## Credit

If you report a valid vulnerability, you will be credited in the
[GitHub Security Advisory](https://docs.github.com/en/code-security/security-advisories/working-with-repository-security-advisories/editing-a-repository-security-advisory#about-credits-for-security-advisories)
for the fix, which also credits you on the published CVE record when one is
issued. Tell me the name or handle you would like to be credited as, or let me
know if you would rather stay anonymous.

There is no paid bug bounty for this project.

---

## Scope

This is a command-line tool that reads Markdown and templates from your machine
and produces a PDF. Reports are most relevant when they involve:

- Reading or writing files outside the intended input and output paths, for
  example through a crafted image path, bibliography path, or template path.
- Arbitrary code or command execution triggered by a Markdown file, a `.typ`
  template, or front-matter values.
- Crafted input that causes the compiler to hang indefinitely or exhaust memory.

Out of scope:

- Vulnerabilities in dependencies — report those upstream to
  [`typst`](https://github.com/messense/typst-py),
  [`mistune`](https://github.com/lepture/mistune),
  [`click`](https://github.com/pallets/click), or
  [`rich`](https://github.com/Textualize/rich). If a dependency issue affects
  this project specifically, a report here is still useful.
- Crashes and malformed output that carry no security impact. Those are ordinary
  bugs — please [open an issue](https://github.com/leonardosalasd/doc-engine-cli/issues/new).

A `.typ` template is executable input by design: pointing `--template` at a file
means running it. Treat templates from untrusted sources the same way you would
treat any other code you download and run.
