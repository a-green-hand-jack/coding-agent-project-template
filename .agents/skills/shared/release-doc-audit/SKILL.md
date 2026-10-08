---
name: release-doc-audit
description: Audit release documentation, version references and registry paths before tagging.
---

# Release documentation audit

Run this read-only audit from the repository root before creating a release tag.
Pass the release tag being prepared as `TARGET_TAG` in the commands below. The
skill is usable by the template repository and by downstream projects after
adapting the repository URL and release-note ownership.

1. Confirm the target release identity and version record:

   ```bash
   test -n "${TARGET_TAG:?set TARGET_TAG, for example v0.1.6}"
   grep -nE "^## ${TARGET_TAG//./\\.}([[:space:]]|$)" RELEASE_NOTES.md
   grep -A2 '^template:' .agents/content-registry.yaml
   ```

   The registry's `template.version` must equal `TARGET_TAG` for the template
   repository. A downstream project records the template tag it adopted in the
   same field and keeps its own `RELEASE_NOTES.md` separate.

2. Enumerate version-like references and classify every result:

   ```bash
   rg --hidden -n --glob '!*.lock' --glob '!.project/**' --glob '!.git/**' \
     -o 'v[0-9]+\.[0-9]+\.[0-9]+' .
   ```

   Accept a reference only when it is the target release, historical release
   history, or an explicitly illustrative example in a command or skill. A
   copy-ready prompt must use `TARGET_TAG`/`<TEMPLATE_TAG>` or name the release
   being prepared. Record any unclassified reference as a finding and fix it
   before tagging.

3. Check copy-ready prompts and release instructions directly. They must point
   to the target tag or use an explicit placeholder, and must distinguish the
   template repository's release notes from a downstream project's own release
   notes.

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
