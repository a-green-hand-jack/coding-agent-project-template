---
name: issue-workflow
description: Implement one Issue in its own Herdr worktree and agent session dispatched by difficulty (start), merge its PR from the dev checkout (merge), and retire the worktree after the merge (close-out).
---

# Issue workflow

Use this skill when the coordinating agent session (the *dev session*, running
in the primary checkout of the integration branch) starts, merges or retires the
work of one Issue. Each Issue is implemented by a separate agent session in its
own Herdr worktree; the maintainer talks to that session directly in its pane.
That session opens the PR; the dev session merges it after review on GitHub and
then closes the worktree out.

Run **start** when an Issue is ready to implement, **merge** when its PR is
approved, and **close-out** automatically after a verified merge, without waiting
to be asked (exceptions are listed under Close-out).

## Adaptation slots

Fill these from the destination project before first use, and never run a
command that still contains a placeholder. Everything else in this skill is
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
| `<MERGE_METHOD>` | `gh pr merge` method flag. Close-out's ancestry check assumes a merge commit. | `--merge` |
| `<CI>` | Whether CI covers the project's checks. `yes`: rely on PR checks and the base-branch run. `no`: run `<POST_MERGE_CHECK>` in the dev checkout. | project fact |
| `<POST_MERGE_CHECK>` | Verification commands from `DEV.md`, used when `<CI>` is `no`. | `DEV.md` verification strategy |
| `<PRE_MERGE_GATE>` | Optional read-only product command that must pass before merging, for example `<cmd> archive --check`. | none |
| `<ARCHIVE_CMD>` | Product command that archives and registers non-rebuildable results before a worktree is retired. | none |
| `<MONITOR_CMD>`, `<STOP_CMD>` | Product commands that list live runs in a worktree and stop one. | none |

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
- Herdr syntax below was checked against herdr 0.9.1. Run `herdr worktree --help`,
  `herdr agent --help` and `herdr pane --help`; the installed CLI is authoritative.
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

   If the count is not 0, run `git -C <dev> pull --ff-only` first.
2. Choose the tier, model and effort as described in
   [Dispatch by difficulty](#dispatch-by-difficulty) and make sure the Issue body
   has a matching Dispatch section; write or correct it now if it does not.
3. Create the worktree with Herdr's native command. Omit `--path` and keep the
   default location:

   ```bash
   herdr worktree create --workspace "$HERDR_WORKSPACE_ID" \
     --branch <branch> --base <BASE> --no-focus
   ```

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
6. Generate the handoff prompt and add the Issue-specific section below. Write it
   to `<worktree>/.project/state/initial-prompt.md`, which avoids shell quoting
   and leaves a handoff record, then deliver it and confirm the agent started:

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

### Issue-specific section appended to the handoff prompt

```text
Also read first:
- `gh issue view <N> --comments` for the discussion;
- <other files, linked Issues or references to read first>

Scope: <what to do; what explicitly not to do>
Acceptance: <the Issue's acceptance evidence>
<Optional parallel-work note: files other worktrees may also touch; make small,
append-only edits there>

Constraints:
- Work only on Issue #<N>; record out-of-scope findings and report them instead
  of fixing them;
- Follow AGENTS.md: no credentials or machine-private paths; local state only
  under this worktree's .project/;
- Do not commit or push until the maintainer asks. Then open the PR from this
  worktree (repository `<REPO>`, base `<BASE>`) and do not merge it;
- <If `<PRE_MERGE_GATE>` is defined: run it before opening the PR and fix what it lists>;
- When finished, report with `git status` and `git diff --stat`, say what was
  verified and what was not, and wait for confirmation.
```

## Merge

The dev session merges PRs into `<BASE>`. Several PRs may be open at once and
conflict, for example when each appends to the same index. Resolve those
conflicts in the dev checkout. Do not ask the Issue sessions to rebase or merge
`<BASE>` into their branches, and do not enter their worktrees.

Handle one PR at a time and re-check the next one after each merge.

1. Update the dev checkout: `git -C <dev> pull --ff-only` (locate `<dev>` as in
   Close-out step 1).
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
   PR's remote branch:

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
6. Close out the PR's worktree (below).

## Close-out

Run after a merge whose step 5 passed, without waiting for a request. Do not
close out, and report to the maintainer instead, when:

- the PR deliberately only references its Issue (`Refs #N`) and the Issue stays
  open, because the work continues;
- the maintainer said to keep the worktree;
- a precondition in step 3 or 5 fails: uncommitted changes, unpushed commits, an
  agent still working or a live task.

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
   squash- or rebase-merges cannot pass the ancestry check; it replaces that line
   with its own evidence that the branch's content reached `<BASE>` and records the
   evidence in the report.
4. Bring the dev checkout's `<BASE>` up to date so it contains the merged PR
   (step 6 copies state into it and step 8's `branch -d` judges against it):

   ```bash
   git -C <dev> pull --ff-only
   ```

   Stop and report if `<dev>` is not on `<BASE>`, local changes block the pull, or
   local `<BASE>` has diverged from `origin/<BASE>`. Do not merge, rebase or reset
   to force it. Conflicts between PRs belong to Merge, not here.
5. Confirm nothing is running. `herdr pane list --workspace <ws>` must show the
   agent as `idle` or `done`. When `<MONITOR_CMD>` is defined, run it in
   `<worktree>`; a live run goes to the maintainer, and is stopped only through
   `<STOP_CMD>`.
6. Migrate local state and asset links to the dev checkout:

   ```bash
   (cd <worktree> && bash .agents/scripts/teardown-worktree.sh --migrate-to <dev>)
   ```

   The script prints `inspect-state.sh` output, then `migrate-assets.sh` copies
   `.project/state`, `runs`, `artifacts` and `manifest` into
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
