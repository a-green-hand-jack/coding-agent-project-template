---
name: template-harvest
description: Discover reusable practice that downstream adopters have already settled and bring it back into this template.
---

# Template harvest

Maintainer-only procedure for this template repository; it is registered as
`scope: template` and must never be copied into a downstream project. It covers
the direction the other template channels do not: `template-feedback` is an
adopter reporting a defect, and `template-adoption` / `template-upgrade` move the
template into an adopter. Harvest goes looking, on purpose, for what adopters
have already settled on their own (a skill, a shared memory record, a script fix,
a registry model change) and decides with evidence whether it belongs upstream.

## Boundaries

- This repository is public; the adopter set is not. An adopter's name, path,
  private decision or raw log never enters a tracked file, Issue, PR, commit
  message or memory record here. Use a local id and counts ("two adopters").
- Adopters are read-only. Use `git --no-optional-locks -C <path>` with `show`,
  `ls-tree`, `log`, `cat-file`, `rev-parse`, `worktree list` and
  `status --porcelain`. Never fetch, pull, check out, stash, commit, or run an
  adopter's own scripts or CLI. The only writes are to the ignored local state
  below. Use the existing CLIs directly (`cli-first-operations`); do not add a
  scanner script or a scheduled job.
- Harvest decides what the template should gain. Landing it in an adopter is
  `template-upgrade`.

## Local state

Everything lives in this worktree's ignored `.project/` and is per device
(`git check-ignore -v .project/state/harvest` must report the ignore rule).

- `.project/state/harvest/roots`: one directory per line to scan on this device
  (the canonical project root and the linked-worktree root). Create it on first
  use; never scan temporary directories.
- `.project/state/harvest/adopters.yaml`: the adopter set and watermarks.
- `.project/runs/harvest-<date>/`: the inventories and report of one run.

```yaml
adopters:
  - id: adopter-1            # local alias; the only name allowed in Issues and memory
    owner: <resolved repository path>
    aliases: [<symlinks or renamed paths resolving to the same repository>]
    worktrees: [<linked worktrees>]
    state: settled | in-progress | unresolvable
    integration_branch: dev
    scanned_commit: <short sha>
    pin: <template tag> | needs-backfill
    pin_source: registry | DEV.md | git-history
    watermark: null          # integration-branch sha whose delta is fully classified
    landing:                 # filled once a candidate becomes a template change
      - { candidate: <template Issue>, release: <tag>, status: pending | landed }
```

## 1. Discover adopters

1. Read this template's own marker:
   `sed -n '/^template:/,/^[^[:space:]]/p' .agents/content-registry.yaml`.
2. Enumerate checkouts one and two levels below each root and group them by the
   owning repository. `--path-format=absolute` is required: without it
   `--git-common-dir` is relative to the current directory and aliases do not
   collapse.

   ```bash
   for p in <root>/* <root>/*/*; do
     [ -e "$p/.git" ] || continue
     real=$(cd "$p" && pwd -P)
     common=$(git --no-optional-locks -C "$real" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) \
       || { echo "unresolvable: $p"; continue; }
     printf '%s\t%s\t%s\n' "$p" "$real" "$common"
   done
   ```

   Equal `common` values are one adopter: a symlinked or renamed checkout and its
   linked worktrees count once. A `.git` pointer to a missing git directory is
   `unresolvable`; record it, but it is neither an adopter nor a source.
3. Recognize an adopter, strongest evidence first:
   - **Registry marker.** `git show <integration>:.agents/content-registry.yaml`
     has a `template:` block whose `repository` equals this template's.
   - **Pre-marker adopter.** The registry has no `template:` block, or there is
     no registry. Do not skip it. Require a template reference in the fixed files
     `AGENTS.md DEV.md README.md USER.md .agents/AGENTS.md` (never a recursive
     grep; large repositories make it unusable) or an
     `.agents/scripts/setup-worktree.sh`. Recover the pin from `DEV.md` and from
     `git log --grep=<template name>` (an "adopt ... <tag>" commit), record
     `pin: needs-backfill` with its source, and confirm it by diffing against
     that tag. A bare `.agents/` directory is not a marker.
4. Set `state`. `settled`: the marker is reachable from the integration branch
   (`dev`, else the default branch). `in-progress`: the marker exists only on a
   feature branch, in the index or in a worktree while the integration branch
   lacks it (`git cat-file -e <integration>:.agents/content-registry.yaml` fails
   but the file exists). Only `settled` integration-branch content is a harvest
   source; unmerged or uncommitted work can still be reverted. Record in-progress
   adopters and note visible model changes (new registry fields, another memory
   layout) as watch items for the next run.
5. Record each adopter's pin, tags behind the current release, and cleanliness
   (`git status --porcelain`). Resolve the integration branch to a commit once,
   store it as `scanned_commit`, and use that sha for every later read: a live
   adopter's branch can move mid-run.

## 2. Delta inventory

Compare each adopter's `scanned_commit` with the template at its pin and at the
current release, and with this repository's `dev`: an unreleased change is
already upstream.

```bash
blobs() { git --no-optional-locks -C "$1" ls-tree -r "$2" -- .agents AGENTS.md CLAUDE.md DEV.md | awk '{print $4"\t"$3}' | LC_ALL=C sort; }
```

`blobs <adopter> <scanned_commit>` against `blobs <template> <pin>` gives the
*added* paths (absent at the pin) and *modified* paths (different blob); against
`blobs <template> <current>` it gives the paths the adopter is *missing* (drift).
Count product content (`memory/project/`, `knowledge/project/`, product
background in `AGENTS.md`) without reading it in depth, then examine the rest:

1. Content in two or more adopters and absent here. Compare paths and blob ids,
   and establish provenance with `git log --diff-filter=A -- <path>`: a commit
   that follows another repository's form, or identical or near-identical blobs,
   marks a port. A port and its source are one origin.
2. `memory/shared/` and `knowledge/shared/` records, and legacy flat memory that
   claims to be shared.
3. `.agents/scripts/**` and `.agents/tests/**` changes and extension points
   (`setup-project.sh`, sourced helpers). Read the diff. A comment that calls a
   change a temporary downstream fix points at a template Issue to look up.
4. Registry model changes: top-level keys, `classes`, entry fields, `scope` values.
5. Non-product rules added to the adopter's `AGENTS.md` (skip project background).

After the first run, review only
`git log <watermark>..<integration> -- .agents AGENTS.md CLAUDE.md DEV.md`. A
watermark that is not an ancestor of the branch means a first run again.

## 3. Classify

Give each delta, or each group of identical deltas, exactly one class and cite
the evidence (path, commit, blob id):

- **shared candidate**: passes the generality gate; continue to step 4.
- **adaptation note**: useful structure that depends on adopter tooling; keep
  the points that must stay parameters in the destination skill's adapt list.
- **project-local**: depends on the adopter's product, repository, machine or
  provider; no action.
- **drift**: the adopter is behind the current release, or carries a temporary
  patch for a template defect that is already fixed; it belongs to
  `template-upgrade` for that adopter.
- **already upstream**: in the current release, in this repository's `dev`, or
  tracked by an open or closed template Issue or PR (`gh issue list --state all`,
  `gh pr list --state all`). Record where and stop. A delta can be partly
  upstream; split it.

Generality gate. A delta is a shared candidate only if all of these hold:

1. It still holds after removing the adopter's product, repository, machine,
   provider, CLI and URL names; what is left is parameters, not content.
2. It is a procedure, decision or script behavior. A dated, changeable fact is
   knowledge that needs a source and refresh condition, not a harvested rule.
3. Two independent adopters used it (separate origins, see ports above), or the
   classification states why one use is already general (it implements a rule
   this template already prescribes, or fixes a script every adopter inherits)
   and what observation would show that wrong.
4. It does not contradict an existing template rule.

Diverged copies are the best source of adaptation points: what each copy changed
after the split is what the destination must parameterize.

## 4. Upstream channel

For each shared candidate:

1. Search this repository's Issues and PRs, open and closed, for the same change
   and reuse it when found.
2. Confirm repository visibility (the template is public), then open one Issue
   per candidate with the templates in `.github/ISSUE_TEMPLATE/` (`feature.yml`:
   Problem, Scope and design, Acceptance evidence; `bug.yml` for a defect in a
   template script). State the generic practice, its parameters and adaptation
   points, the destination (`shared/` or `shared_with_adaptation`;
   `memory/shared/` or `memory/project/`), the number and independence of
   adopters as counts, and the compatibility and cleanup impact. Include no
   adopter name, path, private decision or raw log.
3. Implement only under this repository's own Issue, a Herdr-created worktree
   from `dev` and a PR (root `AGENTS.md`). Never from the harvest session and
   never by editing an adopter.
4. When the change ships, record in `adopters.yaml` `landing` which adopter takes
   it in which release through `template-upgrade`. An adopter whose copy diverged
   resolves it there as a local conflict.
5. Record the result as one focused record under `.agents/memory/project/` using
   `project-memory-governance`: counts, gate decisions, Issues opened and the
   release, never the adopter list. Advance an adopter's `watermark` to its
   `scanned_commit` only when every delta in range has a recorded class.

## 5. Release gate and report

Run steps 1-4 before cutting every release (`DEV.md`, release section). If no
adopter is reachable on this device, say so; never infer adopters from project
names. The report states the adopter set (local id, state, pin and its source,
integration commit), delta counts per category, each classification with its
evidence, the Issues opened, and what was not examined. Show that adopters were
only read: the commands were the allow-listed ones above, and no working-tree
file in a settled adopter is newer than the run start. A live adopter's own
sessions touch its `.git` (`index`, `FETCH_HEAD`) concurrently, so file times
there prove nothing either way; do not cite them. A dry run stops after step 3
and leaves every watermark unchanged.
