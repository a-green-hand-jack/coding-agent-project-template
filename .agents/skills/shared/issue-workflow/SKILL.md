---
name: issue-workflow
description: Implement one Issue in its own Herdr worktree and agent session dispatched by difficulty (start), merge its PR from the dev checkout (merge), and retire the worktree after the merge (close-out); small changes are made directly in the dev checkout.
---

# Issue workflow

Use this skill when the coordinating agent session (the *dev session*, running
in the primary checkout of the integration branch) starts, merges or retires the
work of one Issue. Each Issue is implemented by a separate agent session in its
own Herdr worktree; the maintainer talks to that session directly in its pane.
That session opens the PR; the dev session merges it after review on GitHub and
then closes the worktree out.

Run **start** when an Issue is ready to implement, **merge** when its PR is
approved, and **close-out** right after a verified merge. The approval to merge
covers the close-out, so do not wait or ask again (exceptions are listed under
Close-out).

## When this flow is not needed

`AGENTS.md` separates larger units of work from small changes. Larger units (a
new feature, a cross-file or architectural change, isolation and credentials,
public behavior, a long experiment that changes the product, a change that needs
review) use this flow: an Issue, a Herdr worktree and a PR. A *small change*
needs no Issue, worktree or PR; the dev session makes it directly in the dev
checkout, on `<BASE>`. A change is small only when it is one of these:

- documentation or comments;
- memory records and their index entries;
- a spelling fix;
- a fix confined to one file that needs no design decision;
- running an existing command as acceptance, without changing product code.

When unsure, treat the change as larger and use [Start](#start). When a small
change grows or raises a design question, stop: open an Issue for it, continue
under Start, and tell the maintainer which uncommitted edits in the dev checkout
belong to it.

A small change is not committed or pushed automatically either: only when the
maintainer asks. Run the applicable checks and report the evidence, with the
commands and their output. Before editing, run the dev live-run check (Shared
boundaries): while a run is live, nothing the run executes is edited in place
(`long-running-supervision`), so that change waits or becomes an Issue. The other
shared boundaries concern Herdr worktrees and do not apply.

## Adaptation slots

Before first use, write the destination project's values in the
`## In this repository` section at the end of this file, as a table of slot and
value; a slot left out takes its default. Project-specific additions to a step
go in the same section, keyed to the step (see `template-adoption` step 5). Do
not edit this table or the text above that section, and never run a command
that still contains a placeholder. Everything else in this skill is
project-neutral.

| Slot | Meaning | Default |
| --- | --- | --- |
| `<BASE>` | Integration branch that worktrees start from and PRs target. | `dev` |
| `<REPO>` | `owner/name` that owns the Issues and PRs. Pass `--repo <REPO>` to every `gh` call when the clone has no unambiguous default repository. | this repository |
| `<AGENT_KIND>` | Herdr agent kind for the Issue session (`herdr agent start --help` lists them). | project choice |
| `<AGENT_ARGS>` | Arguments after `--` for the agent CLI other than model and effort, such as its permission mode. Take them from that CLI's own `--help` and use only what the maintainer authorized. | none |
| `<MODEL_ARGS>` | The agent CLI's arguments that set the model and reasoning effort, written with `{model}` and `{effort}`. Map the tier efforts onto the values the CLI accepts; where it has no higher level, use its highest. | project choice |
| `<MODEL_LOW>`, `<MODEL_MID>`, `<MODEL_HIGH>` | Models for the dispatch tiers (see Dispatch by difficulty), as the agent CLI names them. | project choice |
| `<EXCLUDED_MODELS>` | Models never dispatched unless the maintainer asks for one by name. | none |
| `<FALLBACK_AGENT>` | Agent kind used only when the primary agent is unavailable, with its own `<AGENT_ARGS>`, `<MODEL_ARGS>` and tier models. | none |
| `<AGENT_PREFIX>` | Short project prefix. The agent name is `<AGENT_PREFIX>-issue-<N>` and must be unique across the whole Herdr server. | project choice |
| `<WORKSPACE_PREFIX>` | Prefix of the Herdr workspace label, so that a server holding worktrees of several repositories shows which repository an Issue workspace belongs to. Herdr accepts upper-case letters in labels but not in agent names, so a project may prefer an upper-case prefix here. | `<AGENT_PREFIX>` |
| `<MERGE_METHOD>` | `gh pr merge` method flag. Close-out's ancestry check assumes a merge commit. | `--merge` |
| `<CI>` | Whether CI covers the project's checks. `yes`: rely on PR checks and the base-branch run; the template's optional `.github/workflows/template-check.yml` is adopted. `no`: run `<POST_MERGE_CHECK>` in the dev checkout; that workflow is left out (`template-adoption` step 3). | project fact |
| `<POST_MERGE_CHECK>` | Verification commands from `DEV.md`, used when `<CI>` is `no`. | `DEV.md` verification strategy |
| `<PRE_MERGE_GATE>` | Optional read-only product command that must pass before merging, for example `<cmd> archive --check`. | none |
| `<ARCHIVE_CMD>` | Product command that archives and registers non-rebuildable results before a worktree is retired. | none |
| `<MONITOR_CMD>`, `<STOP_CMD>` | Product commands that list live runs in a checkout (the dev checkout or a worktree) and stop one. | none |

## Writing conventions

A project declares how it writes in one place, the `writing:` block of
`.agents/content-registry.yaml`:

```yaml
writing:
  language: <working language>
  issue_sections: <first section>, <second section>, ...
```

- `language`: the working language of Issues, PRs, review and Issue comments,
  the Issue-specific section of a handoff prompt, and the human documents
  (`README.md`, `USER.md`, `DEV.md` and the project's release notes).
- `issue_sections`: the sections an Issue body starts with, in order, for
  example the goal and the approach before the details. The project may use
  them as the fields of its own Issue forms; the template's forms in
  `.github/ISSUE_TEMPLATE/` stay as they are.
- Text the template ships keeps the template's language and is never
  translated: the text of shared skills and memory records above their
  `## In this repository` section, script output, and the fixed markers other
  tools read (such as the release notes' upgrade-section marker). Slot values
  and additions in that section may use the working language.
- Without the block, or without a field, nothing is declared for it: each file
  keeps the language it has, and Issues follow the forms' fields.

`new-agent-prompt.sh` prints the declaration into every handoff,
`template-adoption` writes the block, and `template-upgrade` never changes it.

## Phased work

Work that has several phases, each needing its own review, is one parent Issue
with one sub-Issue per phase, so that progress is checked off phase by phase.

1. The parent Issue holds the goal, the phases and a checklist with one line
   per phase (`- [ ] #<C> <phase>`). Phasing does not change scope: every phase
   stays part of the parent's plan, and the parent closes when the last phase
   merges.
2. Each phase is a sub-Issue with its own scope and acceptance, linked to the
   parent with GitHub's sub-issue relation. It goes through [Start](#start),
   [Merge](#merge) and [Close-out](#close-out) like any Issue, and its PR says
   `Closes #<C>` and names the parent.
3. Link a sub-Issue `<C>` to its parent `<P>`:

   ```bash
   parent=$(gh issue view <P> --repo <REPO> --json id --jq .id)
   child=$(gh issue view <C> --repo <REPO> --json id --jq .id)
   gh api graphql -H 'GraphQL-Features: sub_issues' \
     -f query='mutation($parent: ID!, $child: ID!) { addSubIssue(input: {issueId: $parent, subIssueId: $child}) { issue { number } subIssue { number } } }' \
     -f parent="$parent" -f child="$child"
   ```

   `removeSubIssue` with the same input removes the link, and
   `gh issue view <P>` lists the sub-issues. Recent `gh` releases also offer
   `gh issue create --parent <P>` and `gh issue edit <P> --add-sub-issue <C>`
   (see `gh issue edit --help`).

## Shared boundaries

- Require `test "${HERDR_ENV:-}" = 1`. If it fails, the session is not in a
  Herdr-managed pane: report the blocker and stop. Do not fall back to
  `git switch -c`, raw `git worktree add`, another worktree manager or a
  temporary directory.
- Operate only on the workspace, worktree, pane and agent created for this
  Issue. Never close or delete the dev checkout, another Issue's worktree or a
  workspace the maintainer opened.
- Read IDs, paths and state from Herdr's JSON output, never from sidebar order or
  examples. Absolute local paths are used at runtime only; do not write them to
  Git, Issues, PRs or this file.
- Do not routinely use `--trust-repository`, `--force` or `git branch -D`; ask
  the maintainer first.
- If a command fails, times out or leaves unexpected state, inspect with
  `herdr worktree list`, `herdr agent get` and `herdr agent read` before deciding.
  Do not retry blindly.
- Check repository visibility before any write to an Issue, PR or remote branch,
  and keep credentials, private data, local absolute paths and unredacted logs out
  of it.
- Commits, pushes and merges follow `AGENTS.md`: the PR merge needs the
  maintainer's review approval, and a conflict-resolution commit and its push need
  the maintainer's confirmation.
- Initialize the dev checkout once with `bash .agents/scripts/setup-worktree.sh`
  so `.project/home` exists and diagnostics pass there.
- The dev checkout may drive a long-running product run, which fails when a
  pull or merge changes the code under it (see `long-running-supervision`).
  Before every `git pull` or `git merge` in `<dev>` below, run the *dev live-run
  check*: when `<MONITOR_CMD>` is defined, `(cd <dev> && <MONITOR_CMD>)`. A live
  run it lists goes to the maintainer, and the pull or merge waits until the run
  ends or the maintainer decides. Do not stop the run to make way for it.
- Herdr syntax below was checked against herdr 0.9.4; the `worktree create`
  result paths in Start step 3 were last checked against 0.9.1. Run
  `herdr worktree --help`, `herdr agent --help` and `herdr pane --help`; the
  installed CLI is authoritative.
  General Herdr control rules: `herdr --skill`.

## Start

Input: Issue number `<N>` and a branch `<branch>` named per `DEV.md`
(`<type>/issue-<N>-<slug>`, with `<type>` one of `fix`, `feat`, `docs`, `chore`).

1. Confirm the Issue has settled scope and acceptance: `gh issue view <N>`.
   Locate the dev checkout `<dev>` (`.result.source.source_checkout_path`) with
   `herdr worktree list --workspace "$HERDR_WORKSPACE_ID"`, confirm
   `git branch --list <branch>` is empty, then bring `<BASE>` up to date:

   ```bash
   git -C <dev> fetch origin
   git -C <dev> rev-list --count <BASE>..origin/<BASE>
   ```

   If the count is not 0, run the dev live-run check, then
   `git -C <dev> pull --ff-only`.
2. Choose the tier, model and effort as described in
   [Dispatch by difficulty](#dispatch-by-difficulty) and make sure the Issue body
   has a matching Dispatch section; write or correct it now if it does not.
3. Create the worktree with Herdr's native command. Omit `--path` and keep the
   default location:

   ```bash
   herdr worktree create --workspace "$HERDR_WORKSPACE_ID" \
     --branch <branch> --base <BASE> --label <WORKSPACE_PREFIX>-issue-<N> \
     --no-focus
   ```

   The label names the Issue workspace in `herdr workspace list`
   (`herdr worktree list` shows the open workspace id instead). Without it Herdr derives one from the branch, such as
   `issue-12-fix-parser`, which does not say which repository it belongs to.
   Close-out still locates the worktree by branch.

   From the returned JSON record the worktree path `<worktree>`, the workspace
   id `<ws>` and the root pane id `<pane>` (herdr 0.9.1: `.result.worktree.path`,
   `.result.workspace.workspace_id`, `.result.root_pane.pane_id`).
4. Start the agent in the new pane, passing the chosen model and effort
   explicitly through `<MODEL_ARGS>`; never rely on the CLI's default:

   ```bash
   herdr agent start <AGENT_PREFIX>-issue-<N> --kind <AGENT_KIND> --pane <pane> \
     --timeout 60000 -- <AGENT_ARGS> <MODEL_ARGS>
   ```

   - `agent_not_ready` means a dialog blocked startup. Look with
     `herdr agent read <name> --source visible`. If it is the agent's folder-trust
     prompt for this project's own worktree and the maintainer has authorized that
     routine confirmation, confirm the selection, run
     `herdr agent send-keys <name> enter`, then
     `herdr agent wait <name> --timeout 60000` until `idle`. Never answer any
     other dialog; hand it to the maintainer.
   - Read the agent's screen to confirm it runs in the intended mode, and that
     its status line (or the CLI's own model or status command) shows the
     dispatched model and effort. If either differs, do not deliver the prompt;
     report to the maintainer.
5. The new pane is occupied by the agent, so initialize the worktree from the
   dev session's own shell:

   ```bash
   (cd <worktree> && bash .agents/scripts/setup-worktree.sh)
   ```

   Confirm the output's `root:` is `<worktree>` and `branch:` is `<branch>`. Asset
   links come only from what setup creates; do not hand-create them with `ln -s`.
6. Generate the handoff prompt and add the Issue-specific section below. The
   generated part carries the [Issue session rules](#issue-session-rules); the
   appended section adds what is specific to the Issue and never narrows them.
   Write it to `<worktree>/.project/state/initial-prompt.md`, which avoids shell
   quoting and leaves a handoff record, then deliver it and confirm the agent
   started:

   ```bash
   bash .agents/scripts/new-agent-prompt.sh <N> <branch> \
     > <worktree>/.project/state/initial-prompt.md
   # append the Issue-specific section from the template below
   herdr agent prompt <name> "$(cat <worktree>/.project/state/initial-prompt.md)"
   herdr agent wait <name> --until working --until blocked --timeout 30000
   ```

   Do not add `--wait` to `agent prompt`: it blocks until the first turn ends. On
   `blocked`, read the screen and hand it to the maintainer. A timeout does not
   mean the prompt was lost: `herdr agent read <name>` first, never resend blindly.
7. Add the session name and `<branch>` to the Issue's Dispatch section. Report
   `<ws>`, the agent name, `<branch>` and `<worktree>` to the maintainer, who
   switches to that workspace (or uses `herdr agent focus <name>` on request).
   From here the dev session does not edit that worktree.

### Dispatch by difficulty

Judge the Issue by its scope, risk and uncertainty, not by its type (`feat`,
`fix`, `docs`, `chore`). When unsure between two tiers, take the higher one. When
a mistake is costly (credentials, isolation, data loss, externally visible
state), go one tier up.

| Tier | Typical Issue | Model | Effort |
| --- | --- | --- | --- |
| mechanical | Rename, sync documents and indexes, apply a change the Issue already spells out; no design. | `<MODEL_LOW>` | low or medium |
| routine | Feature or fix inside the existing design, several files, decisions already in the Issue, clear acceptance. | `<MODEL_MID>` | medium or high |
| hard | Needs design or judgment: isolation and credentials, processes and concurrency, cross-module change, a new workflow, real runs. | `<MODEL_HIGH>` | high or xhigh |
| hardest | Hard, plus large uncertainty or results that are hard to verify. | `<MODEL_HIGH>` | max |

Do not dispatch a model in `<EXCLUDED_MODELS>` unless the maintainer asks for it.

Worked example for Claude Code (`<AGENT_KIND>` `claude`), whose `--help` lists
the model aliases and the effort levels `low`, `medium`, `high`, `xhigh` and
`max`:

```text
<MODEL_ARGS>  --model {model} --effort {effort}
<MODEL_LOW>   haiku
<MODEL_MID>   sonnet
<MODEL_HIGH>  opus
```

A routine Issue then starts with `-- <AGENT_ARGS> --model sonnet --effort high`.

Record the dispatch in the Issue body as the last section, in this form. A
coordinating session that creates the Issue writes it then; otherwise Start step
2 adds it. Session and branch are added in Start step 7. Never write a workspace
id or local path here.

```markdown
## Dispatch

- agent: <agent and permission mode>
- model: `<model>`; effort: `<effort>`
- reason: <tier>: <the scope, risk or uncertainty that decided it>
- session: `<AGENT_PREFIX>-issue-<N>`, branch `<branch>`
```

Edit the body through a file rather than shell quoting:
`gh issue view <N> --repo <REPO> --json body --jq .body > .project/state/issue-<N>-body.md`,
edit that file, then `gh issue edit <N> --repo <REPO> --body-file .project/state/issue-<N>-body.md`.
The Issue forms in `.github/ISSUE_TEMPLATE/` have no Dispatch field on purpose:
whoever files the Issue cannot judge the dispatch, and the coordinating session
writes the section.

**Fallback.** Use `<FALLBACK_AGENT>` only when the primary agent is unavailable:
out of quota, logged out or in an outage. Not for difficulty or preference. Keep
the tier and take the fallback's model for it. If `<FALLBACK_AGENT>` is not
defined, report the blocker to the maintainer.

**Re-dispatch.** Any later change of agent, model or effort, including a
fallback, updates the agent, model, effort and session lines and appends one
line that keeps the history:

```markdown
- re-dispatched: <previous agent, model, effort> → <new ones>: <reason>
```

### Issue session rules

`new-agent-prompt.sh` prints these rules into every handoff; change both
together.

- **Verify to completion.** The session runs every check the Issue's acceptance
  and the project's CI call for, including real runs and, after a push,
  `gh pr checks`, and reports one definite result with the commands and their
  output. The acceptance bounds the checks: none is skipped, and none is added
  for its own sake. Only a step the maintainer alone can perform (an
  interactive login, a decision) is named, as a blocker that says what the
  maintainer must do. There is no routine "not verified" section, and a check
  that was not run is never claimed.
- **Keep real runs small and sufficient.** Before a real run, judge whether the
  change can affect something the system must keep doing; a change the
  regression checks already cover needs no real run. A run that is needed uses
  the smallest task, the fewest components and a small budget to prove this
  change, reuses evidence that already answers the question, and avoids the
  most expensive providers unless the change concerns them. The plan and the PR
  state what each run proves and why it must run. This does not relax "Verify to
  completion": every check the acceptance calls for still runs.
- **Fix what you meet.** A defect met while solving the Issue that blocks it or
  is related to it is fixed in the same worktree, verified, and listed in the
  PR. That is part of the Issue, not an unrequested feature. Only an unrelated,
  larger problem is reported for a separate Issue.
- **Other worktrees are not its concern.** Parallel worktrees are expected to
  change the same files, and the dev checkout resolves conflicts at
  [Merge](#merge). The session completes its Issue fully and does not narrow its
  change to avoid conflicts.
- **Merge implies close-out.** The approval to merge the PR covers its
  [Close-out](#close-out): right after the verified merge, the dev session
  migrates `.project/` and removes the worktree without asking again. Results
  that cannot be rebuilt are archived before the merge.
- **Write in the declared language.** When the registry declares
  [writing conventions](#writing-conventions), the session writes Issues, PRs,
  comments and human documents in that language and starts Issue bodies with
  the declared sections; template text keeps its language. The generated
  handoff carries this rule only when a language is declared.

### Issue-specific section appended to the handoff prompt

```text
Also read first:
- `gh issue view <N>` for the Issue and `gh issue view <N> --comments` for the
  discussion (outside a terminal, `--comments` prints only the comments);
- <other files, linked Issues or references to read first>

Scope: <everything in the Issue's scope; what the Issue explicitly excludes>
Acceptance: <the Issue's acceptance evidence, as the checks to run>

Constraints:
- Follow AGENTS.md: no credentials or machine-private paths; local state only
  under this worktree's .project/;
- Do not commit or push until the maintainer asks. Then open the PR from this
  worktree (repository `<REPO>`, base `<BASE>`) and do not merge it;
- <If `<PRE_MERGE_GATE>` is defined: run it before opening the PR and fix what it lists>;
- When finished, report the result with its evidence, `git status` and
  `git diff --stat`, and wait for confirmation.
```

## Merge

The dev session merges PRs into `<BASE>`. Several PRs may be open at once and
conflict, for example when each appends to the same index. Resolve those
conflicts in the dev checkout. Do not ask the Issue sessions to rebase or merge
`<BASE>` into their branches, and do not enter their worktrees.

Handle one PR at a time and re-check the next one after each merge.

1. Update the dev checkout (locate `<dev>` as in Close-out step 1). Run the dev
   live-run check first; with a live run, stop here and report, before pulling.
   Otherwise `git -C <dev> pull --ff-only`.
2. Inspect the PR:

   ```bash
   gh pr view <PR> --repo <REPO> --json state,baseRefName,headRefName,mergeable,mergeStateStatus
   ```

   `state` must be `OPEN` and the base `<BASE>`. Maintainer approval must be
   visible on the PR or the Issue; without it, do not merge and report. When `<CI>`
   is `yes`, `gh pr checks <PR> --repo <REPO>` must be green.
3. Run the pre-merge gate when `<PRE_MERGE_GATE>` is defined. Locate `<worktree>`
   as in Close-out step 1, then `(cd <worktree> && <PRE_MERGE_GATE>)`.
   - Passing: continue.
   - Failing: **do not merge.** Report the output. Fixing it is the Issue
     session's work, since the dev session does not edit another worktree: ask the
     maintainer to have that session fix it and push to the PR branch, then
     re-check from step 2.
   - Continue past a failing gate only on the maintainer's explicit decision. Record
     what was deferred; Close-out handles it.
   - A gate command that itself errors (missing tool, missing worktree) is a
     failure to report, not a pass.
4. Merge. When `mergeable` is `MERGEABLE`, run
   `gh pr merge <PR> --repo <REPO> <MERGE_METHOD>` without `--delete-branch`;
   Close-out deletes the branch. Then do step 5 and Close-out before the next PR.

   When `mergeable` is `CONFLICTING`, resolve it in the dev checkout using the
   PR's remote branch. Run the dev live-run check again first, since a run may
   have started after step 1; with a live run, stop and report before merging.

   ```bash
   git -C <dev> fetch origin
   git -C <dev> merge --no-ff origin/<branch>
   ```

   Resolve per file, `git add`, then `git commit`; `git -C <dev> merge --abort`
   backs out. Keep both sides of a mechanical conflict (both appended index
   lines). For a semantic conflict, where the two sides decided the same thing
   differently, do not choose: list both sides for the maintainer. Create the
   merge commit and `git push origin <BASE>` only after the maintainer confirms.
   Then `gh pr view <PR> --repo <REPO> --json state` must show `MERGED`; if not,
   report and do not push again.
5. Verify the merged `<BASE>`. When `<CI>` is `yes`, confirm the run for the merge
   succeeded: `gh run list --repo <REPO> --branch <BASE> --limit 1`. When `no`, run
   `<POST_MERGE_CHECK>` in `<dev>`. On failure, report the output; do not patch
   around it in the dev session.
6. Close out the PR's worktree (below) right away.

## Close-out

The maintainer's approval to merge covers the close-out. Run it immediately after
a merge whose step 5 passed and report the result; do not ask again. Only the
decisions the steps below hand to the maintainer (ignored files outside
`.project/`, a commit on `<BASE>`) still wait for them. Do not close out, and
report to the maintainer instead, when:

- the PR deliberately only references its Issue (`Refs #N`) and the Issue stays
  open, because the work continues;
- the maintainer said to keep the worktree;
- a precondition in step 3, 4 or 5 fails: uncommitted changes, unpushed commits,
  a live run in the dev checkout, an agent still working or a live task in the
  worktree (a live run or a container mounting it).

Removing a worktree closes its workspace panes, so run these steps from another
workspace, normally the dev checkout's.

1. Locate. `herdr worktree list --workspace "$HERDR_WORKSPACE_ID"` gives
   `<dev>` as `.result.source.source_checkout_path` (confirm its listed branch is
   `<BASE>`); the entry whose branch is `<branch>` gives `<worktree>` (`.path`)
   and `<ws>` (`.open_workspace_id`). If `<ws>` is empty, run
   `herdr worktree open --workspace "$HERDR_WORKSPACE_ID" --path <worktree> --no-focus`
   and take `<ws>` from its result. Stop and report if the entry is missing or
   `<ws>` equals `$HERDR_WORKSPACE_ID`.
2. Confirm the PR merged and the Issue closed:

   ```bash
   gh pr view <PR> --repo <REPO> --json state,baseRefName,headRefName
   gh issue view <N> --repo <REPO> --json state
   ```

   The PR must be `MERGED` with base `<BASE>` and head `<branch>`. If the Issue is
   still `OPEN` only because the PR lacked `Closes #<N>`, close it with
   `gh issue close <N> --repo <REPO> --comment "Resolved by #<PR>."`.
3. Confirm the branch reached `<BASE>` and the worktree is clean:

   ```bash
   git -C <dev> fetch origin --prune
   git -C <dev> merge-base --is-ancestor <branch> origin/<BASE>
   git -C <worktree> status --porcelain
   ```

   The second command must exit 0 and the third must print nothing (the ignored
   `.project/` is handled in step 6). Stop and report otherwise. A project that
   squash- or rebase-merges cannot pass the ancestry check; it writes its own
   evidence that the branch's content reached `<BASE>` in the
   `## In this repository` section, keyed to this step, uses it instead, and
   records the evidence in the report.
4. Bring the dev checkout's `<BASE>` up to date so it contains the merged PR
   (step 6 copies state into it and step 8's `branch -d` judges against it).
   Run the dev live-run check first, then:

   ```bash
   git -C <dev> pull --ff-only
   ```

   Stop and report if `<dev>` is not on `<BASE>`, local changes block the pull, or
   local `<BASE>` has diverged from `origin/<BASE>`. Do not merge, rebase or reset
   to force it. Conflicts between PRs belong to Merge, not here.
5. Confirm nothing is running. `herdr pane list --workspace <ws>` must show the
   agent as `idle` or `done`. When `<MONITOR_CMD>` is defined, run it in
   `<worktree>`; a live run goes to the maintainer, and is stopped only through
   `<STOP_CMD>`. Then list the containers that mount the worktree, which
   `<MONITOR_CMD>` does not see (a stopped run kept for resume, a background job):

   ```bash
   (cd <worktree> && bash .agents/scripts/inspect-state.sh)
   ```

   Its `## containers mounting this worktree` section names every container,
   running or stopped, with a mount whose source is inside `<worktree>`. Exit 3
   means it found one, or an installed runtime could not be queried; each is a
   live task that goes to the maintainer. Do not stop or remove the container.
   With no container runtime installed the section prints `skip` and the check
   passes.
6. Migrate local state and asset links to the dev checkout:

   ```bash
   (cd <worktree> && bash .agents/scripts/teardown-worktree.sh --migrate-to <dev>)
   ```

   The script prints `inspect-state.sh` output (and exits 3 without migrating
   when step 5's container check fails), then `migrate-assets.sh` copies
   `.project/state`, `runs`, `artifacts`, `manifest` and the entries
   `.agents/scripts/migrate-project.rules` marks `copy` into
   `<dev>/.project/migrations/<worktree-dir>-<UTC-timestamp>/`, and copies
   untracked `assets/` entries (asset links) into `<dev>/assets/`. Tracked files
   arrive through Git, and it refuses to overwrite a different existing destination
   asset. It deletes nothing. On success its last line is
   `ready for managed worktree removal; no source directory was deleted`; note the
   `migration=` path. On a non-zero exit, stop, keep the worktree and report the
   full output.

   The script does not copy ignored files outside `.project/`. Read the
   `git status --short --ignored` section of its output and decide each such file
   with the maintainer.

   The migration directory is temporary custody, not storage. Results that cannot
   be rebuilt (run records, outputs, transcripts) must be archived to external
   storage and registered following `asset-lifecycle`: use `<ARCHIVE_CMD>`, ideally
   in the worktree before the merge. If archiving after the merge changes tracked
   files in the dev checkout (for example `assets/MANIFEST.yaml`), commit that change
   on `<BASE>` with the maintainer's confirmation and reference the Issue; do not
   leave the dev checkout dirty. If no command covers a result, do not write glue
   scripts (see `cli-first-operations`): report the gap and where the data lives so
   an Issue can add the command.
7. Remove the worktree with `herdr worktree remove --workspace <ws>`. Confirm the
   returned path is `<worktree>`. Do not add `--force`; if it is refused, report
   the reason.
8. Delete the branches:

   ```bash
   git -C <dev> branch -d <branch>
   git -C <dev> push origin --delete <branch>
   ```

   If `-d` is refused, report the reason and do not use `-D`. Skip the second
   command when the remote branch is already gone.
9. Verify and report each step's output as evidence:
   - `herdr worktree list --workspace "$HERDR_WORKSPACE_ID"` no longer lists
     `<branch>`;
   - `git -C <dev> branch --list <branch>` and
     `git -C <dev> ls-remote --heads origin <branch>` print nothing;
   - `git -C <dev> rev-list --count <BASE>..origin/<BASE>` is 0;
   - `<dev>/.project/migrations/` holds this run's directory, and no unique copy of
     a result remains only in the retired worktree;
   - non-rebuildable results are archived and registered, or the gap is reported.

This skill provides process, not permission: it cannot override the project's
permission configuration or `AGENTS.md`.
