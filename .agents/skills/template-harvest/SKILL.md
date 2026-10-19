---
name: template-harvest
description: Discover reusable practice that downstream adopters have already settled, read only through GitHub, and bring it back into this template.
---

# Template harvest

Maintainer-only procedure for this template repository; it is registered as
`scope: template` and must never be copied into a downstream project. It covers
the direction the other template channels do not: `template-feedback` is an
adopter reporting a defect, and `template-adoption` / `template-upgrade` move the
template into an adopter. Harvest goes looking, on purpose, for what adopters
have already settled on their own (a skill, a shared memory record, a script fix,
a registry model change) and decides with evidence whether it belongs upstream.

Adopters are inspected and contacted through GitHub only: discovery, pins and
deltas come from `gh`, and requests to an adopter go to its Issues. No local
checkout of an adopter is scanned, resolved or needed.

## Boundaries

- This repository is public; the adopter set is not. An adopter's name, private
  decision or raw log never enters a tracked file, Issue, PR, commit message or
  memory record here. Use a local id and counts ("two adopters").
- Adopters are read-only. The allowed reads are `gh repo list`, `gh repo view`,
  `gh issue list`, `gh pr list`, `gh search commits`, and `gh api` GET requests
  on `repos/<repo>` and its `branches`, `commits`, `compare`, `contents`,
  `git/trees` and `git/blobs`. `gh api` turns a request with `-f`, `-F` or
  `--input` into a POST, so put query parameters in the URL and never pass those
  flags or a `-X` other than `GET`. Never clone, fork, push, open a PR, or change
  files or settings in an adopter, and never run its scripts or CLI. The one
  write to an adopter is an Issue or a comment on one (step 5). Use the existing
  CLIs directly (`cli-first-operations`); do not add a scanner script or a
  scheduled job.
- Harvest decides what the template should gain. Landing it in an adopter is
  `template-upgrade`, run in that adopter's own repository.

## Local state

Everything lives in this checkout's ignored `.project/`
(`git check-ignore -v .project/state/harvest` must report the ignore rule).

- `.project/state/harvest/adopters.yaml`: the adopter set and watermarks, keyed
  by GitHub repository.
- `.project/runs/harvest-<date>/`: the probe output, inventories and report of
  one run.

```yaml
owners: [<GitHub account or organization whose repositories are probed>]
last_run: <UTC time of the last completed discovery>
adopters:
  - id: adopter-1            # local alias; the only name allowed in Issues and memory here
    repo: <owner/name>       # the key; never a local path
    visibility: private | public
    state: settled | in-progress | unresolvable
    integration_branch: dev
    scanned_commit: <sha>
    pin: <template tag> | needs-backfill
    pin_source: registry | DEV.md | commit-history
    watermark: null          # integration-branch sha whose delta is fully classified
    landing:                 # filled once a candidate becomes a template change
      - { candidate: <template Issue>, release: <tag>, status: pending | landed }
    requests:                # Issues opened in the adopter from step 5
      - { issue: <number>, kind: upgrade | feedback, release: <tag>, status: open | closed }
```

`owners` defaults to the authenticated account (`gh api user --jq .login`).
A record from the earlier local-path layout (`owner:` a path, `aliases`,
`worktrees`) is converted on first use: its `scanned_commit` resolves with
`gh api repos/<repo>/commits/<sha>` only in the repository that holds it. Keep
`id`, `pin`, `watermark` and `landing`, set `repo`, and drop the path fields.

The helpers below are used in steps 1 and 2. Define them in the shell of the
run; they wrap `gh` and `git` and are not saved as a script.

```bash
plane() { awk -F'\t' '$1 ~ /^\.agents\// || $1 ~ /^(AGENTS|CLAUDE|DEV)\.md$/' | LC_ALL=C sort; }
remote_blobs() {  # <repo> <sha>: development-plane path and blob id
  gh api "repos/$1/git/trees/$2?recursive=1" \
    --jq 'if .truncated then error("tree truncated") else (.tree[] | select(.type == "blob") | "\(.path)\t\(.sha)") end' | plane
}
template_blobs() { git ls-tree -r "$1" | awk '{print $4"\t"$3}' | plane; }  # <template tag or branch>
delta() {  # <template blobs> <adopter blobs>
  awk -F'\t' 'NR==FNR{t[$1]=$2;next} {seen[$1]=1; if(!($1 in t)) print "added\t"$1; else if(t[$1]!=$2) print "modified\t"$1} END{for(p in t) if(!(p in seen)) print "missing\t"p}' "$1" "$2" | LC_ALL=C sort
}
read_file() { gh api -H 'Accept: application/vnd.github.raw+json' "repos/$1/contents/$3?ref=$2"; }  # <repo> <sha> <path>
```

GitHub tree entries carry git blob ids, so `remote_blobs` compares directly
with `template_blobs` from this repository's tags. A truncated tree is an error,
not a smaller adopter; read that repository's directories one by one instead.

## 1. Discover adopters

1. Confirm `gh auth status` shows the maintainer's account, and read this
   template's own marker:
   `sed -n '/^template:/,/^[^[:space:]]/p' .agents/content-registry.yaml`.
   `git fetch --tags origin` so every release tag is available locally.
2. List each owner's repositories:

   ```bash
   gh repo list <owner> --limit 1000 --source --no-archived \
     --json nameWithOwner,visibility,defaultBranchRef,pushedAt \
     > .project/runs/harvest-<date>/repos.json
   ```

   Probe every repository in the set and every repository whose `pushedAt` is
   newer than `last_run` (all of them on a first run). Do not rely on GitHub
   code search: on 2026-10-19 it returned no result for this template's own
   registry file, so a repository is recognized only by reading its file.
3. Recognize an adopter, strongest evidence first. Read the registry on `dev`,
   then on the default branch. Test `gh api`'s own exit status, not a pipeline's:
   a 404 (the branch has no registry) exits non-zero, which a following `sed`
   would hide.

   ```bash
   if body=$(gh api -H 'Accept: application/vnd.github.raw+json' \
       "repos/<repo>/contents/.agents/content-registry.yaml?ref=<branch>" 2>/dev/null); then
     sed -n '/^template:/,/^[^[:space:]]/p' <<<"$body"
   else
     echo "no registry on <branch>"
   fi
   ```

   - **Registry marker.** A `template:` block whose `repository` equals this
     template's. Its `version` is the pin. This repository carries the marker
     too; it is not an adopter.
   - **Pre-marker adopter.** No `template:` block, or no registry. Do not skip
     it. Require a template reference in the fixed files
     `AGENTS.md DEV.md README.md USER.md .agents/AGENTS.md` (read each with
     `read_file`; never a recursive search) or an
     `.agents/scripts/setup-worktree.sh` in the tree. Recover the pin from
     `DEV.md` or from an "adopt ... <tag>" commit
     (`gh search commits "<template name>" --repo <repo>`), record
     `pin: needs-backfill` with its source, and confirm it by comparing
     `remote_blobs` with `template_blobs <tag>`. A bare `.agents/` directory is
     not a marker.
4. Set `state`. `settled`: the marker is on the integration branch (`dev`, else
   the default branch). `in-progress`: the integration branch lacks it but a
   branch or an open PR has it. Look only where the integration branch has an
   `.agents/` directory or an open PR touches it
   (`gh pr list --repo <repo> --state open --json number,headRefName,files`),
   then read the registry on those branches. Only `settled` integration-branch
   content is a harvest source; unmerged work can still be reverted, and
   unpushed work is invisible here by design. Record in-progress adopters and
   note visible model changes (new registry fields, another memory layout) as
   watch items for the next run. `unresolvable`: a repository in the set that
   no longer answers (deleted, renamed away, access lost); record it, but it is
   neither an adopter nor a source.
5. Resolve the integration branch to a commit once,
   `gh api repos/<repo>/branches/<branch> --jq .commit.sha`, store it as
   `scanned_commit`, and use that sha for every later read: a live adopter's
   branch can move mid-run. Record visibility, the pin and the tags it is behind
   the current release.

## 2. Delta inventory

Compare each adopter's `scanned_commit` with the template at its pin and at the
current release, and with this repository's `dev`: an unreleased change is
already upstream.

```bash
remote_blobs <repo> <scanned_commit> > adopter.tsv
template_blobs <pin> > pin.tsv; template_blobs <current> > current.tsv
delta pin.tsv adopter.tsv       # added and modified since the pin
delta current.tsv adopter.tsv   # missing: what the adopter lacks of the release
```

A `missing` path that is template-only content (`scope: template` in the
registry, this repository's `memory/project/` and `knowledge/project/`) is
expected and is not drift. A file with an `## In this repository` section always
differs by blob: compare only the text above the section with the pin
(`read_file` at both, or `git show <pin>:<path>` here), and read the section as
the adopter's adaptations.
Count product content (`memory/project/`, `knowledge/project/`, product
background in `AGENTS.md`) without reading it in depth, then examine the rest
with `read_file`:

1. Content in two or more adopters and absent here. Compare paths and blob ids,
   and establish provenance from the commit that added the path, the last entry
   of `gh api "repos/<repo>/commits?sha=<scanned_commit>&path=<path>&per_page=100" --paginate --jq '.[].sha'`:
   a commit that follows another repository's form, or identical or
   near-identical blobs, marks a port. A port and its source are one origin.
2. `memory/shared/` and `knowledge/shared/` records, and legacy flat memory that
   claims to be shared.
3. `.agents/scripts/**` and `.agents/tests/**` changes and extension points
   (`setup-project.sh`, sourced helpers). Read the diff. A comment that calls a
   change a temporary downstream fix points at a template Issue to look up.
4. Registry model changes: top-level keys, `classes`, entry fields, `scope` values.
5. Non-product rules added to the adopter's `AGENTS.md` (skip project background).

After the first run, review only the range from the watermark:

```bash
gh api "repos/<repo>/compare/<watermark>...<scanned_commit>" \
  --jq '.status, (.commits[] | "\(.sha[0:7]) \(.commit.message | split("\n")[0])"), (.files[] | "\(.status)\t\(.filename)")'
```

Keep the files under `.agents/`, `AGENTS.md`, `CLAUDE.md` and `DEV.md`, and read
each one's change with `--jq '.files[] | select(.filename == "<path>") | .patch'`.
A `status` of `identical` means nothing changed; `ahead` is the normal case. A
status of `behind` or `diverged` means the watermark is not an ancestor of the
branch: a first run again. The compare response lists at most 300 files and 250
commits; when it reaches either limit, compare `remote_blobs` at the watermark
and at `scanned_commit` with `delta` instead.

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
  `template-upgrade` for that adopter, requested in step 5.
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

Adopters' `## In this repository` sections (`template-adoption` step 5) are the
best source of adaptation points: an addition that several adopters make to the
same step is a slot or step the template lacks. Text changed above a section, or
an adapted copy without one, is drift for `template-upgrade`, or evidence that a
template step is wrong when adopters had to replace it rather than extend it.

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
   adopter name, private decision or raw log.
3. Implement it after the harvest run, as root `AGENTS.md` sorts the work: a
   larger unit through that Issue, a Herdr-created worktree from `dev` and a PR;
   a small change directly in the dev checkout, citing the Issue. Never by
   editing an adopter.
4. When the change ships, record in `adopters.yaml` `landing` which adopter takes
   it in which release; step 5 asks the adopter for the upgrade. An adopter whose
   copy diverged resolves it there as a local conflict.
5. Record the result as one focused record under `.agents/memory/project/` using
   `project-memory-governance`: counts, gate decisions, Issues opened and the
   release, never the adopter list. Advance an adopter's `watermark` to its
   `scanned_commit` only when every delta in range has a recorded class.

## 5. Requests to adopters

Upgrade requests and feedback reach an adopter as an Issue in its own
repository, opened only for the requests the maintainer approved in this run:

- **Upgrade request**: the adopter is behind a release that lands something it
  needs (`landing`, or drift from step 3). Name the current pin, the target tag
  with a link to this repository's release notes, the items that concern it, and
  `template-upgrade` as the procedure.
- **Feedback**: a question or observation about the adopter's own delta, for
  example a temporary patch the template now fixes, or a candidate whose
  generality needs the adopter's confirmation.

Before writing, search the adopter's open Issues
(`gh issue list --repo <repo> --state open --search "<template name> in:title"`)
and comment on an existing request instead of opening a second one. Check
`visibility` again: a public adopter's Issue is public. Write only about that
adopter and this template; never name another adopter or copy its content, and
include no credentials, local paths or raw logs. Record each Issue in
`requests`. The adopter's own sessions answer and upgrade in its repository; the
next run reads the outcome from the Issue state and the new pin. Feedback from an
adopter to the template arrives here as a `template-feedback` Issue and is
classified as already upstream in step 3.

## 6. Release gate and report

Run steps 1-5 before cutting every release (`DEV.md`, release section). If `gh`
is not authenticated as the maintainer, or no adopter is found, say so; never
infer adopters from repository names. The report in
`.project/runs/harvest-<date>/` states the adopter set (local id, visibility,
state, pin and its source, scanned commit), delta counts per category, each
classification with its evidence, the Issues opened here and in adopters, and
what was not examined. Show that adopters were only read: the commands were the
allowed reads above, and the only writes to an adopter are the Issues and
comments listed in `requests`. A dry run stops after step 3, opens no Issue and
leaves every watermark unchanged.
