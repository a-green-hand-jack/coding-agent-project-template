# Shared memory rules and index

This directory contains durable decisions that are neutral enough to reuse
across projects. Every record is a separate Markdown file with the fields in
[`../entry-template.md`](../entry-template.md), registry-owned lifecycle and scope. A record that names parameters for the destination is
registered `shared_with_adaptation`; the destination writes their values in a
trailing `## In this repository` section (see `template-adoption` step 5), and
the record's own text never contains that heading line.

<!-- registry-index:start -->
- [docker-objects-prefixed-and-removed.md](docker-objects-prefixed-and-removed.md) — Prefix project Docker objects and remove expired owned objects without force.
- [host-files-owned-by-running-user.md](host-files-owned-by-running-user.md) — Keep host artifacts owned by the running user and stop at foreign ownership.
- [issue-close-out.md](issue-close-out.md) — Complete or transfer outstanding duties before migrating and retiring an Issue worktree.
- [issue-dispatch-by-difficulty.md](issue-dispatch-by-difficulty.md) — Record agent, provider, model and effort selected by difficulty and cost.
- [issue-in-herdr-worktree.md](issue-in-herdr-worktree.md) — Implement each Issue in its own verified Herdr worktree and independent agent session.
- [llm-credentials.md](llm-credentials.md) — Keep stable shared credentials and project-owned refreshing logins behind local paths.
- [look-at-the-artifact-before-concluding.md](look-at-the-artifact-before-concluding.md) — Inspect referenced artifacts before concluding from automated metrics.
- [product-state-root.md](product-state-root.md) — Resolve worktree-local product state from the project marker.
- [project-positioning-before-layout.md](project-positioning-before-layout.md) — Establish users, deliverables and domain concepts before choosing paths.
- [provider-cost-routing.md](provider-cost-routing.md) — Use the cheapest capable provider/model and record why each real run is needed.
- [resolve-real-paths-before-moving.md](resolve-real-paths-before-moving.md) — Prove source and destination differ before moving or replacing assets.
- [run-settings-from-config.md](run-settings-from-config.md) — Resolve, record and reuse run configuration with an explicit override order.
- [screen-with-scriptable-fakes.md](screen-with-scriptable-fakes.md) — Screen boundary failures with data-driven fakes before applicable real acceptance.
- [serve-the-coding-agent.md](serve-the-coding-agent.md) — Adapt guidance, commands, isolation, trace and accounting to the project.
- [speed-and-parallelism-by-measurement.md](speed-and-parallelism-by-measurement.md) — Measure concurrency, remove repeated work and retain every required check.
- [third-party-llm-compat-patches.md](third-party-llm-compat-patches.md) — Fill PATCH_DIR for the project's patches or wrappers of third-party LLM tools; they run on every run and state that metrics, prompts and reasoning effort are unchanged.
<!-- registry-index:end -->
