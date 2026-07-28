---
title: Payments API
subtitle: Integration Guide · v1.1
author: Platform Team
template: technical
accent: teal
---

# Payments API

A short, self-contained guide that shows what `doc-engine` turns Markdown into:
front matter for metadata, task lists, footnotes, tables, and highlighted code —
all from a single `README.md`.

## Getting started

Create a charge by posting an amount in the smallest currency unit[^minor]:

```bash
curl https://api.example.com/v1/charges \
  -H "Authorization: Bearer $API_KEY" \
  -d amount=4200 \
  -d currency=usd
```

The call returns a charge object with a stable `id` you can safely retry against.

## Status codes

| Code | Meaning | Retry? |
|---|---|---|
| `200` | Charge succeeded | No |
| `402` | Card declined | No |
| `429` | Rate limited | Yes, with backoff |
| `503` | Temporary outage | Yes |

## Release checklist

- [x] Idempotency keys on every write
- [x] Webhook signatures verified
- [ ] Sandbox tenants migrated
- [ ] Rotate the staging API key

> Charges are immutable once created. To adjust an amount, refund the original
> charge and create a new one.

[^minor]: For example, `4200` means **$42.00** in USD. Zero-decimal currencies
like JPY use the whole number.
