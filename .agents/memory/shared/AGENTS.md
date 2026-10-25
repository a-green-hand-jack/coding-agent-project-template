# Shared memory rules and index

This directory contains durable decisions that are neutral enough to reuse
across projects. Every record is a separate Markdown file with the fields in
[`../ENTRY_TEMPLATE.md`](../ENTRY_TEMPLATE.md), `scope: shared`, and an active
or superseded status. A record that names parameters for the destination is
registered `shared_with_adaptation`; the destination writes their values in a
trailing `## In this repository` section (see `template-adoption` step 5), and
the record's own text never contains that heading line.

## Index

- [`docker-objects-prefixed-and-removed.md`](docker-objects-prefixed-and-removed.md)
  — every image, container, network and volume a project starts in Docker
  carries its prefix; expired ones are removed promptly, only the project's own,
  never with `-f`.
- [`host-files-owned-by-running-user.md`](host-files-owned-by-running-user.md)
  — files, logs, caches and mounted output left on the host belong to the
  running user; no `sudo` for project files; cleanup that meets foreign-owned
  files stops and reports.
- [`issue-in-herdr-worktree.md`](issue-in-herdr-worktree.md) — implement each
  Issue in its own Herdr worktree and agent session, dispatched by the
  coordinator that claimed the Issue; the session verifies to completion, fixes
  related defects and does not narrow its change to avoid conflicts.
- [`issue-close-out.md`](issue-close-out.md) — close out an Issue's worktree
  right after its PR merges; the claiming coordinator resolves conflicts with
  `dev` in the PR's worktree, the merge approval covers the close-out, and live
  runs in the dev checkout or containers mounting the worktree stop it.
- [`issue-dispatch-by-difficulty.md`](issue-dispatch-by-difficulty.md) — dispatch
  each Issue agent with an explicit model and effort for its difficulty tier, and
  record it in the Issue.
- [`look-at-the-artifact-before-concluding.md`](look-at-the-artifact-before-concluding.md)
  — before reporting a generated or evaluated result, look at the artifacts
  yourself next to their references; automatic checks and cross-checks are
  leads, not acceptance evidence; when they disagree, suspect the metric, and
  say what was looked at.
- [`llm-credentials.md`](llm-credentials.md) — share stable LLM credentials
  through one device file; log refreshing logins in once per canonical checkout,
  whose worktrees link to them; never pass a credential as a command-line
  argument; name every credential in a device inventory and the project's
  `credentials.yaml`. Steps in `credential-setup`, formats in
  `credential-inventory`.
- [`product-state-root.md`](product-state-root.md) — product commands resolve
  the worktree's state root from an argument, an environment variable, the
  nearest setup marker (stopping at the repository boundary), then a default.
- [`provider-cost-routing.md`](provider-cost-routing.md) — ordinary tests and
  mechanical work use the cheapest token source and model that can judge them;
  a cheap run is still a real provider-backed run and never replaces a
  capability check; choose agent, provider, model and effort explicitly and
  record them with what the run proves.
- [`resolve-real-paths-before-moving.md`](resolve-real-paths-before-moving.md)
  — before moving, replacing or symlinking a directory, prove source and
  destination are two different places and data sets, and let a person choose
  which copy to delete; the checks are in `asset-lifecycle`.
- [`run-settings-from-config.md`](run-settings-from-config.md) — run parameters
  are settings loaded from configuration with a fixed override order, recorded
  at run start and reused on resume; never constants in code.
- [`screen-with-scriptable-fakes.md`](screen-with-scriptable-fakes.md) — screen
  boundary failure paths before a real run with one scriptable fake (scenarios
  as data, requests recorded with credentials masked by key name, upstream and
  agent-executor boundaries); it is a sieve, not acceptance.
- [`serve-the-coding-agent.md`](serve-the-coding-agent.md) — use the existing
  coding agent and write what serves it: guidance, tools, parallelism, trace
  and cost are the five pillars a change must help at least one of, and each
  project names where they live.
- [`speed-and-parallelism-by-measurement.md`](speed-and-parallelism-by-measurement.md)
  — speed is a quality: independent work runs in parallel and only a real
  dependency queues; concurrency is set from measured resources and provider
  health, reported apart from wall clock and cost; remove repeated work, never a
  check or a spending limit.
- [`third-party-llm-compat-patches.md`](third-party-llm-compat-patches.md) —
  compatibility changes to third-party LLM tools live in the repository and run
  every time; check one captured request body before a batch; no retry-without-
  the-parameter fallbacks.
