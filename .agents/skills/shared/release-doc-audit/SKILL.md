---
name: release-doc-audit
description: Audit release documentation, version references and registry paths before tagging.
---

# Release documentation audit

Run this read-only audit from the repository root before creating a release tag.
Pass the release tag being prepared as `TARGET_TAG` in the commands below. The
skill is usable by the template repository and by downstream projects after
adapting the repository URL, release-note ownership and `RELEASE_HEADING`.

## Adaptation slot

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

1. Confirm the target release identity and version record:

   ```bash
   test -n "${TARGET_TAG:?set TARGET_TAG, for example v0.1.13}"
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

5. Write a short audit report in the release PR with each finding, location,
   classification, resolution or intentional exception. Do not treat a passed
   CI check as evidence that a documentation finding was classified.
