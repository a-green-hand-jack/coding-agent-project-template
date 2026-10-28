---
name: release-doc-audit
description: Write and review self-contained, illustrated release narratives, then audit version references, registry paths and upgrade instructions before tagging.
---

# Release narrative and documentation audit

Use this skill to prepare or review a release page for people, including a
product upgrade, results, a milestone or an archive. A release explains a period
of change; an Issue/PR list supplies provenance, not the explanation. Writing a
draft or running this audit does not authorize a tag, publication or downstream
upgrade. Keep drafts explicitly labelled until publication is authorized.

Run the consistency audit below read-only from the repository root before
tagging. Pass the release being prepared as `TARGET_TAG`. Before a release
heading exists, use `Unreleased` for the upgrade-section check in step 3 and
record that version readiness is pending. Do not invent a version to make a
check pass.

## Adaptation slot

- Record the repository URL, release audience/type, notes ownership, target
  publication surface and its image hosting/rendering support in the destination's
  trailing adaptation section. Use its writing language for the release, without
  translating this shared procedure. Project examples and their images remain
  project-owned content outside this shared skill.
- `RELEASE_HEADING`: extended regular expression that matches the line of the
  project's `RELEASE_NOTES.md` naming `TARGET_TAG`. Default: one `## <tag>`
  heading per release, as the command in step 1 shows.

A downstream project whose notes do not have one such heading per release, for
example because they keep only the current release in the document title, sets
`RELEASE_HEADING` to match its own layout (such as `^# .*${TARGET_TAG//./\\.}([[:space:]]|\$)`).
Keep the pattern anchored to the line that names the release, so that an older
or illustrative tag elsewhere in the file does not satisfy it, and end the tag
the way the default does so that a shorter tag (`v0.4`) does not match a longer
one (`v0.4.0`).

## Prepare the narrative

1. Establish the audience, release claim and comparison baseline. Name the
   previous version and exact candidate commit, what the release covers and
   what it does not. Select the relevant emphasis from
   [release types](references/release-types.md); small releases can use a few
   connected paragraphs and one useful visual rather than a large form.
2. Write in the reader's order: the claim and necessary project background;
   the prior situation; the most consequential changes with examples; evidence
   and what it establishes; how to use, upgrade or obtain the deliverable;
   limitations and next steps. Organize by user consequence, not commit order.
   Explain terms and causal connections in prose; link labels alone do not
   explain why a change matters.
3. Support each substantive claim with inspected artifacts or recorded checks.
   State commands/method, version or run identity, conditions, outcome and limits
   where relevant. Separate historical acceptance from checks of the final
   candidate; name remaining unverified scope and reuse/upgrade conditions.
   A scenario review is not a live run, a diagram is not a screenshot, and
   passing tests do not establish results they do not measure. Preserve the
   project's existing real-run requirements; require model/data fields only
   when they affect this release's claims.
4. Choose visuals that carry information: tables for before/after comparisons,
   flow diagrams for sequence or responsibility, plots for measured results,
   and real redacted screenshots/demos for observable behavior. Give each a
   descriptive caption and explain its relevance in nearby prose. Label
   schematics as such; for results give units, conditions and uncertainty where
   applicable. Add useful alt text or an adjacent text equivalent. Never
   manufacture screenshots, results or decorative numbers.
5. Keep applicable Issue, PR, previous release, fixed commit/version code and
   full compare links in a short reference block at the beginning or end.
   Use immutable code links rather than only a moving development branch.
   Temporarily hide these references and reread: the body must still explain
   what this is, what changed, why it matters, what evidence supports, how to
   use it and its limits. Restore the references before delivery. Public prose
   and images must exclude local paths, secrets and private sources.

## Review the rendered page

Render the actual Markdown on the intended publication surface using existing
tools. Inspect prose, tables, diagrams and image links at normal reading width
and a narrow viewport: check legibility, clipping, captions, alt text and image
accessibility. Where diagrams or relative images do not survive the surface,
provide an accessible static image at a stable URL and verify that URL without
private-session access. A repository-relative image suitable for a checked-in
document may need a fixed raw URL or hosted attachment in a release body.

For a local-only draft, use the platform's renderer/preview when available and
record exactly which surface was inspected. A local HTML preview does not prove
the hosted release layout or remote image availability. Keep rendered artifacts
and observations in the worktree's state directory; report missing tools,
unavailable previews or image hosting precisely, never call a source-only check
a rendering pass. Do not publish merely to obtain a preview.

## Audit release consistency

1. Confirm the target release identity and version record:

   ```bash
   test -n "${TARGET_TAG:?set TARGET_TAG, for example v0.1.15}"
   RELEASE_HEADING="${RELEASE_HEADING:-^## ${TARGET_TAG//./\\.}([[:space:]]|\$)}"
   grep -nE "$RELEASE_HEADING" RELEASE_NOTES.md
   sed -n '/^template:/,/^[^[:space:]]/p' .agents/content-registry.yaml
   ```

   The registry's `template.version` must equal `TARGET_TAG` for the template
   repository, and for a derived template, whose `template` names itself;
   its `template.upstream.version` is the upstream tag it follows, not
   `TARGET_TAG`. A downstream project records the template tag it adopted in
   `template.version` and keeps its own `RELEASE_NOTES.md` separate.

2. Enumerate version-like references and classify every result:

   ```bash
   rg --hidden -n --glob '!*.lock' --glob '!.project/**' --glob '!.git/**' \
     -o 'v[0-9]+\.[0-9]+\.[0-9]+' .
   ```

   Accept a reference only when it is the target release, historical release
   history, the followed template's tag recorded in the registry
   (`template.upstream.version`, or a downstream's `template.version`), or an
   explicitly illustrative example in a command or skill. A
   copy-ready prompt must use `TARGET_TAG`/`<TEMPLATE_TAG>` or name the release
   being prepared. Record any unclassified reference as a finding and fix it
   before tagging.

3. Check copy-ready prompts and release instructions directly. They must point
   to the target tag or use an explicit placeholder, and must distinguish the
   template repository's release notes from a downstream project's own release
   notes.

   A template that other repositories upgrade from (this template, or a
   derived template) also checks the upgrade section of the release entry:
   `### Upgrading ...` must start with `**Command only.**` or list numbered
   manual steps, because `upgrade-template.sh` prints it for every release it
   crosses (`template-upgrade`, "Light path"). Before the release heading
   exists, pass `Unreleased` instead of the tag. A project that is not a
   template skips this check.

   ```bash
   python3 - "$TARGET_TAG" <<'PY'
   import re, sys
   tag = sys.argv[1]
   notes = open("RELEASE_NOTES.md", encoding="utf-8").read()
   entry = next((e for e in re.split(r"^## ", notes, flags=re.M)[1:] if e.split(None, 1)[0] == tag), None)
   if entry is None:
       raise SystemExit(f"RELEASE_NOTES.md has no `## {tag}` entry")
   section = re.search(r"^### Upgrading\b[^\n]*\n(.*?)(?=^### |\Z)", entry, re.M | re.S)
   body = section.group(1).strip() if section else ""
   if not body.startswith("**Command only.**") and not re.search(r"^\d+\. ", body, re.M):
       raise SystemExit(f"`## {tag}`: the `### Upgrading ...` section must start with"
                        " **Command only.** or list numbered manual steps")
   print(f"{tag}: upgrade section marked")
   PY
   ```

4. Verify every path named by a skill or document exists, and verify every
   registry entry points to an existing path. For a quick registry-path check:

   ```bash
   python3 - <<'PY'
   from pathlib import Path
   import yaml
   root = Path('.')
   data = yaml.safe_load(Path('.agents/content-registry.yaml').read_text())
   missing = []
   for entry in data['entries']:
       path = entry['path']
       matches = list(root.glob(path)) if any(ch in path for ch in '*?[') else [root / path]
       if not matches or not any(match.exists() for match in matches):
           missing.append(path)
   if missing:
       raise SystemExit('missing registry paths: ' + ', '.join(missing))
   print('registry paths exist')
   PY
   ```

5. Record findings, locations, classifications, resolutions or intentional
   exceptions, together with the candidate identity, checks and rendered-page
   observations. Use worktree state during local preparation; include the
   report in the release PR when that delivery is authorized. Explicitly
   distinguish a draft, implementation, validation and publication. A passed
   CI check does not classify documentation findings or prove readability.
