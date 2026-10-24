# Shared knowledge rules and index

This directory contains dated facts whose source and refresh condition can be
used across projects. Every record is a separate Markdown file with the fields
in [`../ENTRY_TEMPLATE.md`](../ENTRY_TEMPLATE.md), `scope: shared`, and a
refresh or expiry condition.

## Index

- [`credential-inventory.md`](credential-inventory.md) — the formats of the
  device `inventory.yaml` and the project's `credentials.yaml`, and what
  `probe-credentials.sh --check` and its probes check and print.
- [`gpt5-strict-backend-requests.md`](gpt5-strict-backend-requests.md) — the three
  GPT-5.x request shapes strict Responses backends reject, what to send instead,
  that a relay can hide the rejections, and which common clients produce them.
