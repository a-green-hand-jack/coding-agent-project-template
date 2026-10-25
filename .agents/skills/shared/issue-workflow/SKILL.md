---
name: issue-workflow
description: Several coordinator sessions share the dev checkout, each claiming one Issue; the claimant implements it in its own Herdr worktree and agent session dispatched by difficulty (start), merges its PR after resolving conflicts with the current dev in that worktree (merge), and retires the worktree after the merge (close-out); small changes are made directly in the dev checkout.
---

# Issue workflow

Use this skill when a coordinating agent session (a *coordinator*, running in
the primary checkout of the integration branch, the *dev checkout*) claims,
starts, merges or retires the work of one Issue. Each Issue is implemented by a
separate agent session in its own Herdr worktree; the maintainer talks to that
session directly in its pane. That session opens the PR; the coordinator that
claimed the Issue merges it after review on GitHub and then closes the worktree
out.

Before sending an Issue handoff or follow-up, read the shared
[`agent-communication`](../agent-communication/SKILL.md) skill. It separates
the pane, agent session and conversation/thread, selects Codex's native queue
when its thread is known, and defines the confirmation and stalled-send
evidence required by this workflow.

Run **start** (which first claims the Issue) when an Issue is ready to
implement, **merge** when its PR is approved, and **close-out** right after a
verified merge. The approval to merge covers the close-out, so do not wait or ask
again (exceptions are listed under Close-out).

## Several coordinators

The dev checkout may host several coordinators at once, each in its own Herdr
pane; their number is not limited. Each claims one Issue, with its sub-Issues,
and runs it to the end: it dispatches the worktrees and sessions, follows their
progress, reviews and merges the PRs and closes the worktrees out. Throughout
this skill, *the coordinator* is the one that claimed the Issue at hand.

- One claimant per Issue. A coordinator acts only on the worktrees, sessions,
  PRs and branches of the Issue it claimed; another coordinator's are only read.
- A sub-Issue belongs to the coordinator that claimed its parent.
- An Issue another coordinator claimed is not touched. Taking it over, also
  from a claimant whose pane is gone, is the maintainer's decision.
- An Issue that depends on one another coordinator claimed is recorded with
  blocked-by ([Phased work](#phased-work) step 5) and waits until that Issue is
  merged. Do not enter its worktree and do not press its session; to hurry it,
  ask the maintainer. Its coordinator starts what it blocked ([Close-out](#close-out)
  step 10).
- The dev checkout is common ground; see the shared dev checkout rules under
  [Shared boundaries](#shared-boundaries).

### Claim

1. Have a name others can find in Herdr. If
   `herdr agent get "$HERDR_PANE_ID" | jq -r .result.agent.name` prints `null`,
   name your own pane's agent, unique on the Herdr server:
   `herdr agent rename "$HERDR_PANE_ID" <AGENT_PREFIX>-coord-<N>`.
2. Check that nobody holds the Issue: the Dispatch section of
   `gh issue view <N> --repo <REPO> --json body --jq .body` has no
   `- coordinator:` line, or the line names you. A sub-Issue is claimed only by
   the parent's claimant. If someone else holds it, stop and tell the maintainer.
3. Write `` - coordinator: `<name>` `` as the first line of the Issue's Dispatch
   section, creating the section if needed (edit the body through a file, as in
   [Dispatch by difficulty](#dispatch-by-difficulty)). Read the body again
   before dispatching. There is no lock, so two claims can cross: whichever
   coordinator finds another name on that line, now or later, stops and reports
   to the maintainer.

### See what the other coordinators are doing

These commands only read:

```bash
# open Issues and their claimants
gh issue list --repo <REPO> --state open --limit 100 --json number,title,body \
  --jq '.[] | select(.body | test("(?m)^- coordinator:")) | "#\(.number) \(.body | capture("(?m)^- coordinator: (?<c>.*)$").c) \(.title)"'
# one Issue: its Dispatch section (claimant, sessions, branches) and sub-Issues
gh issue view <N> --repo <REPO>
gh pr list --repo <REPO> --state open
# coordinators and Issue sessions running now, and their state
herdr agent list | jq -r '.result.agents[] | select((.name // "") | startswith("<AGENT_PREFIX>-")) | "\(.name) \(.agent_status) \(.pane_id)"'
# this repository's worktrees, their branches and open workspaces
herdr worktree list --workspace "$HERDR_WORKSPACE_ID" \
  | jq -r '.result.worktrees[] | "\(.branch) \(.open_workspace_id // "-")"'
```

`herdr agent read <name> --source visible` shows a session's screen. Never
prompt, send keys to, rename, focus or close another coordinator's agent or its
Issue sessions.

## When this flow is not needed

`AGENTS.md` separates larger units of work from small changes. Larger units (a
new feature, a cross-file or architectural change, isolation and credentials,
public behavior, a long experiment that changes the product, a change that needs
review) use this flow: an Issue, a Herdr worktree and a PR. A *small change*
needs no Issue, worktree or PR; a coordinator makes it directly in the dev
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
(`long-running-supervision`), so that change waits or becomes an Issue. The
shared dev checkout rules apply as well; the other shared boundaries concern
Herdr worktrees and do not.

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
| `<AGENT_KINDS>` | Herdr agent kinds this project dispatches, in preference order, and the model family each may use: Codex its OpenAI/Codex family, Claude Code its Anthropic family, Pi the family of the provider configured for it. The first usable one is `<AGENT_KIND>`. `herdr agent start --help` lists the installed kinds. | `codex`, `claude`, `pi` |
| `<AGENT_KIND>` | Herdr agent kind for the Issue session: the first usable kind in `<AGENT_KINDS>`. | project choice |
| `<AGENT_ARGS>` | Arguments after `--` for the agent CLI other than provider, model and effort, such as its permission mode. Take them from that CLI's own `--help` and use only what the maintainer authorized. | none |
| `<PROVIDER_ARGS>` | The agent CLI's arguments that select the provider, written with `{provider}`; empty when the provider follows from the model. | none |
| `<MODEL_ARGS>` | The agent CLI's arguments that set the model and reasoning effort, written with `{model}` and `{effort}`. Map the tier efforts onto the values the CLI accepts; where it has no higher level, use its highest. | project choice |
| `<MODEL_SELECTION>` | How a tier's model slot resolves to a concrete model for the chosen agent kind at dispatch time: the series and its version order, how the CLI lists what the account may currently use, what makes a candidate unusable, and the fallback order (see Dispatch by difficulty). | the tier slot's value as written |
| `<MODEL_LOW>`, `<MODEL_MID>`, `<MODEL_HIGH>` | Models for the dispatch tiers (see Dispatch by difficulty), as the agent CLI names them: a model name, an alias, or a series whose newest usable member is resolved at dispatch time. | project choice |
| `<EXCLUDED_MODELS>` | Models and providers never dispatched unless the maintainer asks for one by name. | none |
| `<FALLBACK_AGENT>` | Agent kind used only when the primary agent or its provider is unavailable, with its own `<AGENT_ARGS>`, `<PROVIDER_ARGS>`, `<MODEL_ARGS>` and tier models. | none |
| `<AGENT_PREFIX>` | Short project prefix. The agent name is `<AGENT_PREFIX>-issue-<N>` and must be unique across the whole Herdr server. | project choice |
| `<WORKSPACE_PREFIX>` | Prefix of the Herdr workspace label, so that a server holding worktrees of several repositories shows which repository an Issue workspace belongs to. Herdr accepts upper-case letters in labels but not in agent names, so a project may prefer an upper-case prefix here. | `<AGENT_PREFIX>` |
| `<MERGE_METHOD>` | `gh pr merge` method flag. Close-out's ancestry check assumes a merge commit. | `--merge` |
| `<CI>` | Whether the project adopts the template's optional `.github/workflows/template-check.yml`. `yes`: adopted; its result is read and noted on the PR, never waited for and never a condition (see Merge). `no`: that workflow is left out (`template-adoption` step 3). | project fact |
| `<LOCAL_CHECK>` | The verification commands from `DEV.md`, always filled whatever `<CI>` is. They are the merge gate, run locally; when `<CI>` is `yes` they are the same steps the workflow runs. | `DEV.md` verification strategy |
| `<PRE_MERGE_GATE>` | Optional read-only product command that must pass before merging, for example `<cmd> archive --check`. | none |
| `<ARCHIVE_CMD>` | Product command that archives and registers non-rebuildable results before a worktree is retired. | none |
| `<MONITOR_CMD>`, `<STOP_CMD>` | Product commands that list live runs started in a checkout (the dev checkout or a worktree) and stop one. Close-out stops every run the worktree started through `<STOP_CMD>`, and never through a generic process killer. | none |

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
   merges. The checklist says what the phases are; what must wait for what is
   recorded as blocked-by (step 3), never as a sentence in a body.
2. Each phase is a sub-Issue with its own scope and acceptance, linked to the
   parent with GitHub's sub-issue relation. It goes through [Start](#start),
   [Merge](#merge) and [Close-out](#close-out) like any Issue, and its PR says
   `Closes #<C>` and names the parent. A sub-Issue says who it belongs to
   (sub-issue); blocked-by says what comes first.
3. Before splitting, decide for every two sub-Issues which relation holds, and
   record and dispatch it as the table says:

   | Relation | Record | Dispatch |
   | --- | --- | --- |
   | Parallel: the two are unrelated. | Only the parent link. | Start together. |
   | Serial: B needs the merged code of A. | `gh issue edit <B> --add-blocked-by <A>` | Start B from the new `<BASE>` after A is merged and closed out. |
   | Synchronous: both must land together, because `<BASE>` breaks if either merges alone (an interface changed with all its callers). | Do not split: one sub-Issue, one PR, one worktree. | Start the one Issue. |
   | Asynchronous: B needs only A's interface (a parameter, a file format, a command's output), not its implementation. | Fix the interface first, in the parent Issue or as a small interface sub-Issue. A and B are both blocked-by that interface sub-Issue; an interface written in the parent needs no blocked-by. | Start A and B together once the interface is fixed. |

4. The coordinator that claimed the parent claims every sub-Issue and dispatches
   its worktree. A sub-Issue starts when it has no open blocker
   ([Start](#start) step 1); it does not wait in arrival order
   ([Independent Issues run in parallel](#independent-issues-run-in-parallel)).
   Every sub-Issue starts from the latest `<BASE>`, never from the branch of one
   that has not merged: stacked branches save time only until the earlier PR
   changes, and then cost repeated rebases and conflicts.
5. Link and relate Issues with `gh` (`gh issue create --help`,
   `gh issue edit --help`); the Issue number is the argument, a URL also works:

   ```bash
   # a sub-Issue of <P>, at creation or afterwards
   gh issue create --repo <REPO> --parent <P> --title ... --body-file ...
   gh issue edit <C> --repo <REPO> --parent <P>          # or: gh issue edit <P> --add-sub-issue <C>
   # <B> waits for <A>, at creation or afterwards
   gh issue create --repo <REPO> --blocked-by <A> --title ... --body-file ...
   gh issue edit <B> --repo <REPO> --add-blocked-by <A>  # or: gh issue edit <A> --add-blocking <B>
   # read them
   gh issue view <N> --repo <REPO> --json parent,subIssues,blockedBy,blocking
   # count of blockers that are still open (0: ready to start)
   gh issue view <N> --repo <REPO> --json blockedBy --jq '[.blockedBy.nodes[] | select(.state=="OPEN")] | length'
   ```

   `--remove-parent`, `--remove-sub-issue`, `--remove-blocked-by` and
   `--remove-blocking` undo a link. Closing a blocker does not remove the link;
   the reader counts only blockers whose `state` is `OPEN`. GraphQL's
   `issueDependenciesSummary { blockedBy }` also gives that count.

## Shared boundaries

- Require `test "${HERDR_ENV:-}" = 1`. If it fails, the session is not in a
  Herdr-managed pane: report the blocker and stop. Do not fall back to
  `git switch -c`, raw `git worktree add`, another worktree manager or a
  temporary directory.
- Operate only on the workspaces, worktrees, panes and agents created for the
  Issue you claimed. Never close or delete the dev checkout, another Issue's
  worktree or a workspace the maintainer opened.
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
- The dev checkout is shared by every coordinator:
  - `<BASE>` there moves only by `git pull --ff-only`. Never merge, rebase or
    reset in it, and never leave half-done state there (an unfinished merge,
    uncommitted conflict resolution); conflicts are resolved in the PR's
    worktree ([Merge](#merge)).
  - Uncommitted edits and local commits you did not make belong to another
    coordinator or the maintainer: do not stage, stash, reset, check out or
    commit them.
  - When the maintainer asks to commit a small change, `git add` only the files
    you changed (never `git add -A` or `git add .`), commit, and push at once, so
    the shared `<BASE>` never carries an unpushed commit of yours. A push refused
    because `origin/<BASE>` moved is reported, not forced.
  - When `git pull --ff-only` fails because of someone else's local changes or
    commits, report and wait.
  - Close-out migrates state into `.project/migrations/<worktree-dir>-<UTC-timestamp>/`,
    so close-outs by different coordinators do not overwrite each other.
- The dev checkout may drive a long-running product run, which fails when a
  pull changes the code under it (see `long-running-supervision`). Before every
  `git pull` in `<dev>` below, run the *dev live-run check*: when
  `<MONITOR_CMD>` is defined, `(cd <dev> && <MONITOR_CMD>)`. A live run it lists
  goes to the maintainer, and the pull waits until the run ends or the
  maintainer decides. Do not stop the run to make way for it.
- Herdr syntax in this skill was checked against herdr 0.9.4; the `worktree create`
  result paths in Start step 3 were last checked against 0.9.1. Run
  `herdr worktree --help`, `herdr agent --help` and `herdr pane --help`; the
  installed CLI is authoritative.
  General Herdr control rules: `herdr --skill`.

## Start

Input: Issue number `<N>` and a branch `<branch>` named per `DEV.md`
(`<type>/issue-<N>-<slug>`, with `<type>` one of `fix`, `feat`, `docs`, `chore`).

1. Claim the Issue ([Claim](#claim)) and confirm it has settled scope and
   acceptance: `gh issue view <N>`. Confirm it has no open blocker; if it has,
   do not start it, and report which Issue it waits for:

   ```bash
   gh issue view <N> --repo <REPO> --json blockedBy \
     --jq '.blockedBy.nodes[] | select(.state=="OPEN") | "#\(.number) \(.title)"'
   ```

   It prints nothing when it may start. Locate the dev checkout `<dev>`
   (`.result.source.source_checkout_path`) with
   `herdr worktree list --workspace "$HERDR_WORKSPACE_ID"`, confirm
   `git branch --list <branch>` is empty, then bring `<BASE>` up to date:

   ```bash
   git -C <dev> fetch origin
   git -C <dev> rev-list --count <BASE>..origin/<BASE>
   ```

   If the count is not 0, run the dev live-run check, then
   `git -C <dev> pull --ff-only`.
2. Choose the tier and then the agent kind, provider, model and effort in the
   order [Dispatch by difficulty](#dispatch-by-difficulty) gives, and make sure
   the Issue body has a matching Dispatch section; write or correct it now if it
   does not.
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
4. Start the agent in the new pane, passing the chosen agent kind, provider,
   model and effort explicitly through the slots; never rely on the CLI's
   default:

   ```bash
   herdr agent start <AGENT_PREFIX>-issue-<N> --kind <AGENT_KIND> --pane <pane> \
     --timeout 60000 -- <AGENT_ARGS> <PROVIDER_ARGS> <MODEL_ARGS>
   ```

   - `agent_not_ready` means a dialog blocked startup. Look with
     `herdr agent read <name> --source visible`. If it is the agent's folder-trust
     prompt for this project's own worktree and the maintainer has authorized that
     routine confirmation, confirm the selection, run
     `herdr agent send-keys <name> enter`, then
     `herdr agent wait <name> --timeout 60000` until `idle`. Never answer any
     other dialog; hand it to the maintainer.
   - Confirm the dispatch that actually runs, not the intended one.
     `herdr agent get <name>` gives the agent kind, pane and status; the agent's
     screen, or its own model and status command, shows the provider, model and
     effort it runs. Herdr does not report the model itself, so that output is
     the evidence for it. If kind, provider, model or effort differs from the
     Issue's Dispatch section, do not deliver the prompt: re-dispatch and record
     it, or report to the maintainer.
5. The new pane is occupied by the agent, so initialize the worktree from the
   coordinator's own shell:

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
   From here the coordinator does not edit that worktree, except to resolve a
   conflict at [Merge](#merge) while the Issue session is idle.

### Independent Issues run in parallel

An Issue with no open blocker is started now, whether or not other Issues are
running: each goes through Start in its own worktree and session, by its own
coordinator or, for the sub-Issues of one Issue, by its coordinator. Do not queue
Issues by arrival order. What waits is an Issue that has an open blocker (see
[Phased work](#phased-work) for the relations and how they are recorded). This
changes when sessions start, never the checks each one runs
(`speed-and-parallelism-by-measurement`).

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

Mechanical and routine work take the cheapest token source and model that can
judge it; they are still real provider-backed runs. An expensive provider or
model is used only when the change concerns it: its request format,
authentication or permissions, model capability, quota and error behavior, or
other real behavior only it exercises. The `reason` line then says so (see
`provider-cost-routing`).

### Agent, provider, model and effort

Choose in this order, and pass every value explicitly in Start step 4:

1. **Agent kind.** `<AGENT_KINDS>` lists the kinds this project dispatches, in
   preference order, and the model family each may use; the first usable one is
   `<AGENT_KIND>`. An agent runs only the family its own CLI and configuration
   allow — Codex its OpenAI/Codex models, Claude Code its Anthropic models, Pi
   the models of the provider configured for it. Never tell one CLI to run
   another's model.
2. **Provider and model.** Resolve the tier's model at dispatch time (below),
   then take the provider the account may use for it, passed through
   `<PROVIDER_ARGS>` and `<MODEL_ARGS>`. Do not dispatch a model or provider in
   `<EXCLUDED_MODELS>`, or one the account cannot use, unless the maintainer
   asks for it by name.
3. **Effort.** Take the tier's effort and map it onto the values the CLI
   accepts; where it has no higher level, use its highest.

A tier slot (`<MODEL_LOW>`, `<MODEL_MID>`, `<MODEL_HIGH>`) holds a model name, an
alias or a series. Resolve it before starting the agent, following
`<MODEL_SELECTION>`:

- list the models the agent CLI and the account currently offer (the CLI's own
  `--help`, model or status command);
- discard every candidate that is unusable now: retired, not entitled or out of
  quota for this account, unable to do what the Issue needs, or excluded;
- take the newest member of the tier's series among what remains;
- when the series has no usable member, take the next entry `<MODEL_SELECTION>`
  documents; if none is left, use `<FALLBACK_AGENT>`.

Record the resolved string in the Dispatch section, not the series, and never
leave an old resolved string bound in a slot or in this skill. A substitution is
a re-dispatch and keeps its line.

Worked example for Claude Code (`<AGENT_KIND>` `claude`), whose `--help` lists
the model aliases and the effort levels `low`, `medium`, `high`, `xhigh` and
`max`; the provider follows from the alias, so `<PROVIDER_ARGS>` is empty:

```text
<MODEL_ARGS>  --model {model} --effort {effort}
<MODEL_LOW>   haiku
<MODEL_MID>   sonnet
<MODEL_HIGH>  opus
```

A routine Issue then starts with `-- <AGENT_ARGS> --model sonnet --effort high`.

A project can keep a series in the tier slots instead of one model. With Pi
(`<AGENT_KIND>` `pi`), which runs the models of the provider configured for it,
`<PROVIDER_ARGS>` might be `--provider {provider}` and `<MODEL_ARGS>`
`--model {model} --thinking {effort}`; a project whose `<MODEL_LOW>`,
`<MODEL_MID>` and `<MODEL_HIGH>` hold the `deepseek-v4.1-flash` series dispatches
the newest usable member of that series at that moment, records the resolved
string, and falls back through `<MODEL_SELECTION>` when no member is usable.

Record the dispatch in the Issue body as the last section, in this form. The
coordinator line is written when the Issue is claimed ([Claim](#claim)). A
coordinator that creates the Issue writes the rest then; otherwise Start step 2
adds it. Session and branch are added in Start step 7. Never write a workspace
id, a provider endpoint or local path here.

```markdown
## Dispatch

- coordinator: `<the claiming coordinator's Herdr agent name>`
- agent: <agent kind and permission mode>
- provider: `<provider>`
- model: `<resolved model>`; effort: `<effort>`
- reason: <tier>: <the scope, risk or uncertainty that decided it>, and <why an
  expensive provider or model was needed, when one was>
- session: `<AGENT_PREFIX>-issue-<N>`, branch `<branch>`
```

Edit the body through a file rather than shell quoting:
`gh issue view <N> --repo <REPO> --json body --jq .body > .project/state/issue-<N>-body.md`,
edit that file, then `gh issue edit <N> --repo <REPO> --body-file .project/state/issue-<N>-body.md`.
The Issue forms in `.github/ISSUE_TEMPLATE/` have no Dispatch field on purpose:
whoever files the Issue cannot judge the dispatch, and the coordinator writes
the section.

**Fallback.** Use `<FALLBACK_AGENT>` only when the primary agent or its provider
is unavailable: out of quota, logged out, in an outage, or with no usable model
left in the tier's series. Not for difficulty or preference. Keep the tier and
take the fallback's provider and model for it. If `<FALLBACK_AGENT>` is not
defined, report the blocker to the maintainer.

**Re-dispatch.** Any later change of agent, provider, model or effort, including
a fallback, updates the agent, provider, model, effort and session lines and
appends one line that keeps the history:

```markdown
- re-dispatched: <previous agent, provider, model, effort> → <new ones>: <reason>
```

### Issue session rules

`new-agent-prompt.sh` prints these rules into every handoff; change both
together.

- **Verify to completion.** The session runs every check the Issue's acceptance
  and `<LOCAL_CHECK>` call for, including real runs, and reports one definite
  result with the commands and their output. After a push it may read
  `gh pr checks` and report the CI state (passed, failed or not run), but it
  does not wait for it and does not stop because CI did not run (for example
  for billing); the local result is the evidence. The acceptance bounds the checks: none is skipped, and none is added
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
  name each run's agent, provider, model and effort, what it proves and why it
  must run. This does not relax "Verify to completion": every check the
  acceptance calls for still runs.
- **Route cost first.** Ordinary tests, regression checks, documentation and
  mechanical work use the cheapest token source and model that can judge them;
  an expensive provider or model is used only when the change concerns its
  request format, permissions, capability or real behavior, and the plan says
  why. A cheap run is still a real provider-backed run and never stands in for
  the capability the acceptance must prove. A change of agent, provider, model
  or effort is recorded as a re-dispatch ([Dispatch by difficulty](#dispatch-by-difficulty)).
- **Fix what you meet.** A defect met while solving the Issue that blocks it or
  is related to it is fixed in the same worktree, verified, and listed in the
  PR. That is part of the Issue, not an unrequested feature. Only an unrelated,
  larger problem is reported for a separate Issue.
- **Other worktrees are not its concern.** Parallel worktrees are expected to
  change the same files. At [Merge](#merge) the coordinator resolves this PR's
  conflicts with the current `<BASE>` in this worktree, itself or through this
  session. The session completes its Issue fully and does not narrow its change
  to avoid conflicts.
- **Merge implies close-out.** The approval to merge the PR covers its
  [Close-out](#close-out): right after the verified merge, the coordinator
  migrates `.project/` and removes the worktree without asking again. Results
  that cannot be rebuilt are archived before the merge.
- **Keep its own files in `.project/state/`.** The session's working files
  (plans, PR body drafts, messages to the coordinator) go under
  `.project/state/`, which Close-out always copies, not in the root of
  `.project/`, where a file without a `migrate-project.rules` rule stops the
  migration.
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

### Messages to a running Issue session

The handoff prompt in Start step 6 goes to an agent whose input line is empty.
Every later message from the coordinator is different: the maintainer shares
the pane with the agent and may have a draft typed in its input line.

- **Look before sending.** `herdr agent prompt <name> "..."` appends to whatever
  the input line holds, so a draft and the message merge into one. Before
  sending a follow-up to an agent that is already running, run
  `herdr agent read <name> --source visible` and look at the input line. If it
  is not empty, do not send. Put the message in an Issue comment, or ask the
  maintainer to include it in their own message.
- **Use the communication protocol.** For each follow-up, record the target
  agent session, conversation/thread (when available), selected transport and
  confirmation result. Codex follow-ups use `codex queue --thread <THREAD>
  --message <TEXT>` when the native thread is resolved; Claude Code and Pi use
  `herdr agent prompt`. If Codex's thread cannot be resolved, record the reason
  and the fallback before sending the Herdr prompt. A successful write is not
  proof of receipt: inspect the resulting agent state or native acknowledgement.
- **Do not blind-retry a stall.** After `agent_prompt_stalled`, inspect the
  target with `herdr agent get` and `herdr agent read --source visible`, preserve
  the exact failure and state in `.project/state/` or the Issue, and retry only
  after the input and status preconditions have changed safely.
- **Relay the result and the constraints, not the commands.** When passing on a
  maintainer decision, write the outcome to reach and the constraints it must
  respect. Leave the commands to the project's skills, which know what each
  command can and cannot change. A command named in the relay may not do what
  the coordinator assumed.
- **When the named way does not work,** the Issue session follows the path its
  project documentation gives, says where it deviated and why, and records that
  in the Issue.

## Merge

The coordinator merges the PRs of the Issue it claimed into `<BASE>`. PRs of
several coordinators may be open at once and conflict, for example when each
appends to the same index. Each coordinator resolves the conflicts between its
own PR and the `<BASE>` of that moment, in that PR's own worktree; the dev
checkout is only pulled.

Handle one PR at a time and re-check the next one after each merge. Another
coordinator may merge in between: when `gh pr merge` refuses or `<BASE>` has
moved, go back to step 2.

1. Update the dev checkout (locate `<dev>` as in Close-out step 1). Run the dev
   live-run check first; with a live run, stop here and report, before pulling.
   Otherwise `git -C <dev> pull --ff-only`.
2. Inspect the PR:

   ```bash
   gh pr view <PR> --repo <REPO> --json state,baseRefName,headRefName,mergeable,mergeStateStatus
   ```

   `state` must be `OPEN` and the base `<BASE>`. Maintainer approval must be
   visible on the PR or the Issue; without it, do not merge and report.
   `mergeable` `UNKNOWN` means GitHub is still computing it; query again.

   The gate is `<LOCAL_CHECK>`, not CI. Locate `<worktree>` as in Close-out
   step 1, confirm it is at the PR's latest commit
   (`git -C <worktree> fetch origin` and compare `git -C <worktree> rev-parse HEAD`
   with `gh pr view <PR> --repo <REPO> --json headRefOid --jq .headRefOid`;
   if they differ, `git -C <worktree> merge --ff-only origin/<branch>`), run
   `<LOCAL_CHECK>` there, and leave one comment on the PR with:

   - the commit SHA the checks ran on;
   - each command and its result (pass, or fail with the failing output);
   - the CI state read once with `gh pr checks <PR> --repo <REPO>`: passed,
     failed or not run (for example because Actions could not start). Do not
     wait for it to finish.

   `<LOCAL_CHECK>` all passing and the maintainer's approval are enough to
   merge; if it fails, do not merge, and the Issue session fixes it. A CI
   failure with a passing `<LOCAL_CHECK>` does not block: say so in the PR
   comment and in the report to the maintainer, who decides whether to open an
   Issue to look into the difference. A new head after a push needs this step
   again.
3. Run the pre-merge gate when `<PRE_MERGE_GATE>` is defined. Locate `<worktree>`
   as in Close-out step 1, then `(cd <worktree> && <PRE_MERGE_GATE>)`.
   - Passing: continue.
   - Failing: **do not merge.** Report the output. Fixing it is implementation
     work for the Issue session: ask the maintainer to have that session fix it
     and push to the PR branch, then re-check from step 2.
   - Continue past a failing gate only on the maintainer's explicit decision. Record
     what was deferred; Close-out handles it.
   - A gate command that itself errors (missing tool, missing worktree) is a
     failure to report, not a pass.
4. Merge. When `mergeable` is `MERGEABLE`, run
   `gh pr merge <PR> --repo <REPO> <MERGE_METHOD>` without `--delete-branch`;
   Close-out deletes the branch. Then do step 5 and Close-out before the next PR.

   When `mergeable` is `CONFLICTING`, merge the current `<BASE>` into the PR
   branch in `<worktree>` (located as in Close-out step 1), never in the dev
   checkout. The coordinator does it itself only while the Issue session is
   `idle` or `done` (`herdr agent get <AGENT_PREFIX>-issue-<N>`); otherwise, or
   by choice, it hands the work to the Issue session as described in
   [Messages to a running Issue session](#messages-to-a-running-issue-session),
   with the rules of this step as constraints. When `<MONITOR_CMD>` is defined,
   run it in `<worktree>` first; a live run there goes to the maintainer and the
   merge waits.

   ```bash
   git -C <worktree> status --porcelain
   git -C <worktree> fetch origin
   git -C <worktree> merge origin/<BASE>
   ```

   The first command must print nothing. Resolve per file, `git add`, then
   `git commit`; `git -C <worktree> merge --abort` backs out. Keep both sides of
   a mechanical conflict (both appended index lines). For a semantic conflict,
   where the two sides decided the same thing differently, do not choose: list
   both sides for the maintainer and resolve as they decide. Run
   `<LOCAL_CHECK>` in `<worktree>`. Commit the merge and
   `git -C <worktree> push origin <branch>` only after the maintainer confirms,
   then re-check from step 2: the new head needs `<LOCAL_CHECK>` and its PR
   comment again before `gh pr merge`.
5. Verify the merged `<BASE>`: run the dev live-run check, `git -C <dev> pull --ff-only`,
   then `<LOCAL_CHECK>` in `<dev>`. On failure, report the output; do not patch
   around it in the dev checkout. The CI run on this PR's merge commit is only
   noted in the report, not waited for:

   ```bash
   sha=$(gh pr view <PR> --repo <REPO> --json mergeCommit --jq .mergeCommit.oid)
   gh run list --repo <REPO> --branch <BASE> --commit "$sha"
   ```

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
  a live run in the dev checkout, an agent still working or blocked, a run that
  `<STOP_CMD>` could not stop, a container that mounts the worktree, or state
  that cannot be confirmed.

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
   to force it (see the shared dev checkout rules). Conflicts between a PR and
   `<BASE>` belong to Merge, in the PR's worktree, not here.
5. Stop what this worktree started, before anything is migrated or removed.
   This step's order is fixed: processes stopped, then state and assets
   migrated, then the worktree removed.

   ```bash
   herdr pane list --workspace <ws>
   ```

   The agent must be `idle` or `done`; a `working` or `blocked` agent stops the
   close-out and goes to the maintainer. When `<MONITOR_CMD>` and `<STOP_CMD>`
   are defined, run `<MONITOR_CMD>` in `<worktree>` and stop every run it lists
   through `<STOP_CMD>`, one at a time, then run `<MONITOR_CMD>` again until it
   lists none. Stopping is the default; only a run `<STOP_CMD>` cannot stop, or
   one the maintainer asked to keep, goes to the maintainer. Never use `pkill`,
   `killall`, `fuser -k` or a name pattern: only the project's own `<STOP_CMD>`
   may stop a process, so that a process this worktree did not start is never
   touched.

   Then check what `<MONITOR_CMD>` does not see: host processes, background jobs
   and containers. The run records under `.project/runs/` name each process
   identity; confirm each recorded one is gone (`ps -p <pid>` on the recorded pid,
   never a name pattern). A recorded process that still runs and that
   `<STOP_CMD>` did not stop blocks the close-out. List the containers that mount
   the worktree, running or stopped (a stopped run kept for resume, a background
   job):

   ```bash
   (cd <worktree> && bash .agents/scripts/inspect-state.sh)
   ```

   Its `## containers mounting this worktree` section names every container,
   running or stopped, with a mount whose source is inside `<worktree>`. Exit 3
   means it found one, or an installed runtime could not be queried; each blocks
   the close-out and goes to the maintainer. Do not stop or remove the container.
   With no container runtime installed the section prints `skip` and the check
   passes. Continue only when the agent is idle or done, `<MONITOR_CMD>` lists
   nothing, every recorded process identity is gone and no container mounts the
   worktree; otherwise stop here, keep the worktree and report.
6. Migrate local state and asset links to the dev checkout:

   ```bash
   (cd <worktree> && bash .agents/scripts/teardown-worktree.sh --migrate-to <dev>)
   ```

   The script prints `inspect-state.sh` output (and exits 3 without migrating
   when step 5's container check fails), then `migrate-assets.sh` copies
   `.project/state`, `runs`, `artifacts`, `manifest` and the entries
   `.agents/scripts/migrate-project.rules` marks `copy` (by name or by a
   wildcard such as `plan-*.md`) into
   `<dev>/.project/migrations/<worktree-dir>-<UTC-timestamp>/`, and copies
   untracked `assets/` entries (asset links) into `<dev>/assets/`. Tracked files
   arrive through Git, and it refuses to overwrite a different existing destination
   asset. It deletes nothing. On success its last line is
   `ready for managed worktree removal; no source directory was deleted`; note the
   `migration=` path. On a non-zero exit, stop, keep the worktree and report the
   full output.

   Confirm from the output that the `verified:` count covers `.project/state`,
   `runs`, `artifacts`, `manifest` and every `migrate-project.rules` entry marked
   `copy`, and that the `assets/` section shows each asset link as `copy` or
   `same`. A `CONFLICT`, a `DIFFERS` line or a non-zero exit stops the close-out.
   This verified copy is what step 7 relies on before it removes the worktree.

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
7. Confirm no unique copy is left, then remove the worktree. Every result the
   project must keep is in the step 6 migration directory or archived, the asset
   links resolve in `<dev>`, and no file under `.project/` or `assets/` in
   `<worktree>` is its only copy. Then run
   `herdr worktree remove --workspace <ws>`. Confirm the returned path is
   `<worktree>`. Do not add `--force`; if it is refused, report the reason.
8. Delete the branches:

   ```bash
   git -C <dev> branch -d <branch>
   git -C <dev> push origin --delete <branch>
   ```

   If `-d` is refused, report the reason and do not use `-D`. Skip the second
   command when the remote branch is already gone.

   When the project follows `docker-objects-prefixed-and-removed` and the merged
   PR changed an image or a test fixture, also remove the image tags that only
   this branch used, under that record's rules.
9. Verify and report each step's output as evidence:
   - `herdr worktree list --workspace "$HERDR_WORKSPACE_ID"` no longer lists
     `<branch>`;
   - `git -C <dev> branch --list <branch>` and
     `git -C <dev> ls-remote --heads origin <branch>` print nothing;
   - `git -C <dev> rev-list --count <BASE>..origin/<BASE>` is 0 (when another
     coordinator merged since step 4, repeat step 4 first);
   - `<dev>/.project/migrations/` holds this run's directory, its `verified:`
     line covered `.project/state`, `runs`, `artifacts`, `manifest`, the `copy`
     rules and every asset link, and no unique copy of a result remains only in
     the retired worktree;
   - non-rebuildable results are archived and registered, or the gap is reported.
10. List what this Issue was blocking and start what is now free:

    ```bash
    gh issue view <N> --repo <REPO> --json blocking \
      --jq '.blocking.nodes[] | select(.state=="OPEN") | .number'
    ```

    For each `<M>` it prints, read its open blockers and claimant:

    ```bash
    gh issue view <M> --repo <REPO> --json number,blockedBy,parent,body \
      --jq '"#\(.number) open-blockers=\([.blockedBy.nodes[] | select(.state=="OPEN")] | length) parent=\(.parent.number // "none") claimant=\(.body | capture("(?m)^- coordinator: `?(?<c>[^`\n]*)").c // "none")"'
    ```

    - Claimed by you (or a sub-Issue of an Issue you claimed) and
      `open-blockers=0`: start it ([Start](#start)), from the `<BASE>` just
      pulled.
    - Still has open blockers: leave it; report which Issues it still waits for.
    - Claimed by another coordinator: do not touch it; its coordinator starts it
      ([Several coordinators](#several-coordinators)). Report it to the maintainer
      only when that coordinator is gone.
    - Unclaimed and not a sub-Issue of yours: report it to the maintainer.

This skill provides process, not permission: it cannot override the project's
permission configuration or `AGENTS.md`.
