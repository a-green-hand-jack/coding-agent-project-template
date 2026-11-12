"""Upgrade a project made from an older real release to the release candidate
(this working tree) with the candidate's upgrade-template.sh; the result must
equal a project made from the candidate, except the project's own files."""
from __future__ import annotations

import fnmatch
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[3]
SCRIPT = REPOSITORY / ".agents/scripts/shared/upgrade-template.sh"
sys.path.insert(0, str(REPOSITORY / ".agents/scripts/shared"))
import content_registry as catalog

REGISTRY = ".agents/content-registry.yaml"
IDENTITY = ["-c", "user.name=Test", "-c", "user.email=test@example.invalid"]
OWN_FILES = {"README.md": "# My project\n", "src/app.py": "print('mine')\n", "RELEASE_NOTES.md": "# Release notes\n"}


def git(*args: str, cwd: Path, raw: bool = False):
    result = subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)
    return result.stdout if raw else result.stdout.decode()


def number(tag: str) -> tuple[int, ...]:
    return tuple(int(part) for part in tag[1:].split("."))


def files_of(root: Path) -> dict[str, tuple[str, bytes]]:
    """Each file below ROOT (outside .git and .project) with its kind and content."""
    found = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if relative.parts[0] in (".git", ".project"):
            continue
        if path.is_symlink():
            found[str(relative)] = ("link", os.readlink(path).encode())
        elif path.is_file():
            found[str(relative)] = ("exec" if os.access(path, os.X_OK) else "file", path.read_bytes())
    return found


def without_template_content(root: Path) -> None:
    """Make ROOT, a copy of the template at a tag, a fresh project: drop the
    scope template paths and their registry entries, and the template's own
    writing conventions, which a project replaces with its own or none."""
    registry = root / REGISTRY
    if registry.read_text().startswith('schema_version: 2'):
        data=catalog.loads(registry.read_text())
        excluded=[e for e in data['entries'] if e['scope']=='template']
        for path in files_of(root):
            if any(catalog.rank(path,e['path']) for e in excluded): (root/path).unlink()
        data['entries']=[e for e in data['entries'] if e not in excluded]
        data['omitted']=[{'id':e['id'],'path':e['path'],'reason':'Upstream template-only content; not adopted.'} for e in excluded]
        data.pop('writing',None)
        registry.write_text(catalog.dumps(data))
        catalog.indexes(root,data,write=True)
        return
    lines = registry.read_text(encoding="utf-8").splitlines(keepends=True)
    kept, entry, template_paths = [], [], []

    def flush() -> None:
        body = "".join(entry)
        if re.search(r"^\s+scope: template$", body, re.M):
            template_paths.append(re.match(r"\s*- path:\s*(\S+)", body).group(1))
        else:
            kept.extend(entry)
        entry.clear()

    in_entries = False
    for line in lines:
        if in_entries and re.match(r"^\s*- path:", line):
            flush()
            entry.append(line)
        elif in_entries and entry and line[:1].isspace() and line.strip():
            entry.append(line)
        else:
            flush()
            kept.append(line)
            in_entries = in_entries or line.rstrip() == "entries:"
    flush()
    text = "".join(kept)
    text = re.sub(r"(?:^#.*\n)*^writing:\n(?:^[ \t]+.*\n)*", "", text, flags=re.M)
    registry.write_text(text, encoding="utf-8")
    for pattern in template_paths:
        for path in list(files_of(root)):
            if path == pattern or path.startswith(pattern) and pattern.endswith("/") or fnmatch.fnmatch(path, pattern):
                (root / path).unlink()


class UpgradeFromAnOlderReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory(prefix="upgrade-release-")
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        registry = (REPOSITORY / REGISTRY).read_text(encoding="utf-8")
        current = re.search(r"^template:\n(?:  .*\n)*?  version: (\S+)", registry, re.M).group(1)
        notes = (REPOSITORY / "RELEASE_NOTES.md").read_text(encoding="utf-8")
        unreleased = re.search(r"^## Unreleased\b", notes, re.M) is not None
        self.candidate = current
        if unreleased:
            major, minor, patch = number(current)
            self.candidate = f"v{major}.{minor}.{patch + 1}"
        tags = sorted((tag for tag in git("tag", "-l", "v*", cwd=REPOSITORY).split()
                       if re.fullmatch(r"v\d+\.\d+\.\d+", tag) and number(tag) < number(self.candidate)), key=number)
        self.assertGreaterEqual(len(tags), 2, "the release tags are missing: git fetch --tags origin")
        self.old = tags[-1] if self._testMethodName in ('test_relocated_identity_stops_without_writes', 'test_declared_mapping_preserves_location', 'test_bad_mapping_never_changes_checkout', 'test_mapping_content_conflict_is_atomic', 'test_mapped_deletion_preserves_registry_consistency') else getattr(self, "source_tag", tags[-2])

        # A fixture template repository with the older release and the candidate as its two tags.
        self.template = self.base / "template"
        self.template.mkdir()
        git("init", "-q", cwd=self.template)
        archive = git("archive", self.old, cwd=REPOSITORY, raw=True)
        subprocess.run(["tar", "-x", "-C", str(self.template)], input=archive, check=True)
        self.commit(self.old)
        git("rm", "-rq", ".", cwd=self.template)
        listed = git("ls-files", "-z", "--cached", "--others", "--exclude-standard", cwd=REPOSITORY)
        for name in filter(None, listed.split("\0")):
            source, destination = REPOSITORY / name, self.template / name
            if not (source.exists() or source.is_symlink()):
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            if source.is_symlink():
                os.symlink(os.readlink(source), destination)
            else:
                shutil.copy2(source, destination)
        if unreleased:
            path = self.template / "RELEASE_NOTES.md"
            path.write_text(re.sub(r"^## Unreleased\b.*$", f"## {self.candidate}", path.read_text(encoding="utf-8"),
                                   count=1, flags=re.M), encoding="utf-8")
        if self._testMethodName == 'test_declared_mapping_preserves_location':
            reference = self.template/'.agents/skills/shared/long-running-supervision/SKILL.md'
            reference.write_text(reference.read_text() + '\n[Fake boundary](../../../memory/shared/screen-with-scriptable-fakes.md)\n')
            added = self.template/'.agents/skills/shared/development-writing/references/new-guidance.md'
            added.write_text('# Additional guidance\n')
        if self._testMethodName == 'test_mapping_content_conflict_is_atomic':
            changed = self.template/'.agents/memory/shared/screen-with-scriptable-fakes.md'
            changed.write_text(changed.read_text().replace('# Screen failure paths with a scriptable fake before the real run', '# Changed upstream heading'))
        if self._testMethodName == 'test_mapped_deletion_preserves_registry_consistency':
            path='.agents/memory/shared/screen-with-scriptable-fakes.md'
            data=catalog.loads((self.template/REGISTRY).read_text())
            entry=next(e for e in data['entries'] if e['path']==path)
            data['entries'].remove(entry)
            data.setdefault('omitted',[]).append({'id':entry['id'],'path':path,'reason':'Removed upstream.'})
            (self.template/path).unlink()
            (self.template/REGISTRY).write_text(catalog.dumps(data))
            catalog.indexes(self.template,data,write=True)
        self.commit(self.candidate)

    def commit(self, tag: str) -> None:
        registry = self.template / REGISTRY
        text = registry.read_text(encoding="utf-8")
        text = re.sub(r"^(template:\n  repository: ).*$", lambda m: m.group(1) + str(self.template), text,
                      count=1, flags=re.M)
        text = re.sub(r"^(template:\n(?:  .*\n)*?  version: )\S+", lambda m: m.group(1) + tag, text,
                      count=1, flags=re.M)
        registry.write_text(text, encoding="utf-8")
        git("add", "-A", cwd=self.template)
        git(*IDENTITY, "commit", "-qm", tag, cwd=self.template)
        git("tag", tag, cwd=self.template)

    def project(self, tag: str, own: bool) -> Path:
        root = self.base / f"project-{tag}"
        root.mkdir()
        archive = git("archive", tag, cwd=self.template, raw=True)
        subprocess.run(["tar", "-x", "-C", str(root)], input=archive, check=True)
        without_template_content(root)
        if own:
            for name, text in OWN_FILES.items():
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text(text, encoding="utf-8")
        git("init", "-q", cwd=root)
        return root

    def test_mapped_deletion_preserves_registry_consistency(self) -> None:
        project=self.project(self.old,own=True)
        registry=project/REGISTRY;data=catalog.loads(registry.read_text())
        source='.agents/memory/shared/screen-with-scriptable-fakes.md'
        destination='.agents/memory/shared/local-fake-guidance.md'
        entry=next(e for e in data['entries'] if e['path']==source)
        (project/source).rename(project/destination);entry['path']=destination
        data['path_mappings']=[{'from':source,'to':destination}]
        registry.write_text(catalog.dumps(data));catalog.indexes(project,data,write=True)
        file=project/destination;original=file.read_text();file.write_text(original+'\nLocal content.\n')
        before=files_of(project)
        conflict=subprocess.run(['bash',str(SCRIPT),'--resolved','.agents/memory/project/AGENTS.md',self.candidate],cwd=project,text=True,capture_output=True)
        self.assertNotEqual(conflict.returncode,0)
        self.assertEqual(before,files_of(project))
        file.write_text(original)
        result=subprocess.run(['bash',str(SCRIPT),'--resolved','.agents/memory/project/AGENTS.md',self.candidate],cwd=project,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertFalse((project/destination).exists())
        check=subprocess.run(['bash','.agents/scripts/shared/check-development.sh'],cwd=project,text=True,capture_output=True)
        self.assertEqual(check.returncode,0,check.stdout+check.stderr)

    def test_mapping_content_conflict_is_atomic(self) -> None:
        project = self.project(self.old, own=True)
        registry = project / REGISTRY
        data = catalog.loads(registry.read_text())
        source = '.agents/memory/shared/screen-with-scriptable-fakes.md'
        destination = '.agents/memory/shared/local-fake-guidance.md'
        entry = next(e for e in data['entries'] if e['path'] == source)
        (project/source).rename(project/destination)
        file = project/destination
        file.write_text(file.read_text().replace('# Screen failure paths with a scriptable fake before the real run', '# Different local heading'))
        entry['path'] = destination
        data['path_mappings'] = [{'from':source, 'to':destination}]
        registry.write_text(catalog.dumps(data));catalog.indexes(project, data, write=True)
        before = files_of(project)
        result = subprocess.run(['bash', str(SCRIPT), '--resolved', '.agents/memory/project/AGENTS.md', self.candidate], cwd=project, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('mapped upgrade preflight failed', result.stderr)
        self.assertEqual(before, files_of(project))

    def test_bad_mapping_never_changes_checkout(self) -> None:
        project = self.project(self.old, own=True)
        registry = project / REGISTRY
        data = catalog.loads(registry.read_text())
        source = '.agents/memory/shared/screen-with-scriptable-fakes.md'
        for mappings in (
            [{'from':source,'to':'../escape.md'}],
            [{'from':source,'to':'.agents/memory/shared/serve-the-coding-agent.md'}],
            [{'from':source,'to':'.agents/memory/shared/local.md'}, {'from':source,'to':'.agents/memory/shared/other.md'}],
        ):
            data['path_mappings'] = mappings
            registry.write_text(catalog.dumps(data))
            before = files_of(project)
            result = subprocess.run(['bash', str(SCRIPT), self.candidate], cwd=project, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(before, files_of(project))

    def test_declared_mapping_preserves_location(self) -> None:
        project = self.project(self.old, own=True)
        registry = project / REGISTRY
        data = catalog.loads(registry.read_text())
        source = '.agents/memory/shared/screen-with-scriptable-fakes.md'
        destination = '.agents/memory/shared/local-fake-guidance.md'
        entry = next(e for e in data['entries'] if e['path'] == source)
        (project/source).rename(project/destination)
        entry['path'] = destination
        data['path_mappings'] = [{'from': source, 'to': destination}]
        references = '.agents/skills/shared/development-writing/references/'
        local_references = '.agents/skills/shared/development-writing/local-references/'
        cases = references + 'four-cases.md'
        local_cases = '.agents/skills/shared/development-writing/local-four-cases.md'
        (project/cases).rename(project/local_cases)
        (project/references).rmdir()
        data['path_mappings'] += [{'from': references, 'to': local_references}, {'from': cases, 'to': local_cases}]
        registry.write_text(catalog.dumps(data))
        catalog.indexes(project, data, write=True)
        result = subprocess.run(['bash', str(SCRIPT), '--resolved', '.agents/memory/project/AGENTS.md', self.candidate], cwd=project, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((project/source).exists())
        self.assertTrue((project/destination).exists())
        self.assertTrue((project/local_cases).exists())
        self.assertTrue((project/local_references/'new-guidance.md').exists())
        self.assertIn('(local-four-cases.md)', (project/'.agents/skills/shared/development-writing/SKILL.md').read_text())
        self.assertIn('../../../memory/shared/local-fake-guidance.md', (project/'.agents/skills/shared/long-running-supervision/SKILL.md').read_text())
        after = catalog.loads(registry.read_text())
        self.assertEqual(next(e for e in after['entries'] if e['id'] == entry['id'])['path'], destination)
        check=subprocess.run(['bash','.agents/scripts/shared/check-development.sh'],cwd=project,text=True,capture_output=True)
        self.assertEqual(check.returncode,0,check.stdout+check.stderr)
        before=files_of(project)
        again=subprocess.run(['bash',str(SCRIPT),self.candidate],cwd=project,text=True,capture_output=True)
        self.assertEqual(again.returncode,0,again.stdout+again.stderr)
        self.assertEqual(before,files_of(project))

    def test_relocated_identity_stops_without_writes(self) -> None:
        project = self.project(self.old, own=True)
        registry = project / REGISTRY
        data = catalog.loads(registry.read_text())
        entry = next(e for e in data['entries'] if e['path'] == '.agents/memory/shared/screen-with-scriptable-fakes.md')
        original = project / entry['path']
        moved = original.with_name('local-fake-guidance.md')
        original.rename(moved)
        entry['path'] = str(moved.relative_to(project))
        registry.write_text(catalog.dumps(data))
        before = files_of(project)
        for arguments in (['--check'], []):
            result = subprocess.run(['bash', str(SCRIPT), *arguments, self.candidate], cwd=project, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('locally relocated path', result.stderr)
            self.assertEqual(before, files_of(project))

    def test_the_upgrade_equals_a_project_made_from_the_candidate(self) -> None:
        upgraded = self.project(self.old, own=True)
        before = files_of(upgraded)
        result = subprocess.run(["bash", str(SCRIPT), self.candidate], cwd=upgraded, capture_output=True,
                                text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Refused (conflicts): 0", result.stdout)
        self.assertIn(f"template.version: {self.old} -> {self.candidate}", result.stdout)

        fresh = files_of(self.project(self.candidate, own=False))
        after = files_of(upgraded)
        owned = set(re.findall(r"^  (\S+): project-owned", result.stdout, re.M)) | set(OWN_FILES)
        # A path that is new and optional is left out unless the project adopts it
        # (template-adoption step 3): the command reports it as manual and writes
        # nothing, so such a path differs from the fresh project without being a
        # difference the upgrade is responsible for.
        unadopted = set(re.findall(r"^  (\S+): new optional content in ", result.stdout, re.M))
        differing = {path for path in fresh.keys() | after.keys() if fresh.get(path) != after.get(path)}
        # Catalog provenance and derived indexes intentionally differ when old
        # project history survives. Compare authoritative content separately.
        derived = {REGISTRY} | {p for p in fresh if p.endswith('/AGENTS.md') and '<!-- registry-index:start -->' in fresh[p][1].decode(errors='replace')}
        manual = set(re.findall(r"^  (\S+): changed in .*this command never touches it", result.stdout, re.M))
        self.assertEqual(differing - owned - unadopted - derived - manual, set(), result.stdout)
        for path in manual:
            self.assertEqual(after.get(path),before.get(path))
        for path in derived - {REGISTRY}:
            def rules(raw):
                return re.sub(r'<!-- registry-index:start -->.*?<!-- registry-index:end -->','',raw.decode(),flags=re.S)
            self.assertEqual(rules(after[path][1]),rules(fresh[path][1]),path)
        check=subprocess.run(['bash','.agents/scripts/shared/check-development.sh'],cwd=upgraded,text=True,capture_output=True)
        self.assertEqual(check.returncode,0,check.stdout+check.stderr)
        again=subprocess.run(['bash',str(SCRIPT),self.candidate],cwd=upgraded,text=True,capture_output=True)
        self.assertEqual(again.returncode,0,again.stdout+again.stderr)
        self.assertEqual(files_of(upgraded),after, 'repeat upgrade must be byte-for-byte idempotent')
        for path in unadopted:
            self.assertIn(path, fresh)
            self.assertNotIn(path, after)
        for path in owned:
            actual,original=after.get(path),before.get(path)
            if original and path.startswith(('.agents/memory/','.agents/knowledge/')):
                # The migration removes only registry-owned frontmatter mirrors.
                original=(original[0],re.sub(rb'^(scope|status|supersedes|superseded_by|refresh_after):[^\n]*\n',b'',original[1],flags=re.M))
            self.assertEqual(actual, original, f"{path}: preserve project body and source evidence")
        actual=catalog.loads(after[REGISTRY][1].decode())
        self.assertFalse(any('note' in entry for entry in actual['entries']))
        expected=catalog.loads(fresh[REGISTRY][1].decode())
        self.assertEqual(actual['template'],expected['template'])
        self.assertEqual(actual['schema_version'],2)
        by_path={e['path']:e for e in actual['entries']}
        if self.old == 'v0.1.25':
            # A schema1 project may own the former template-maintainer memory.
            # The template-only rename must not move or overwrite that file.
            old = '.agents/memory/project/template-work-runs-on-codex.md'
            new = '.agents/memory/project/template-dispatch-decisions.md'
            self.assertIn(old, after)
            self.assertNotIn(new, after)
            self.assertEqual(by_path[old]['scope'], 'project')
            upstream = next(e for e in catalog.loads((REPOSITORY / REGISTRY).read_text())['entries'] if e['path'] == new)
            self.assertNotEqual(by_path[old]['id'], upstream['id'])
        for e in expected['entries']:
            self.assertEqual(by_path[e['path']],e)
        source_registry = git('show', f'{self.old}:{REGISTRY}', cwd=self.template)
        if not source_registry.startswith('schema_version: 2'):
            self.assertIn('local_legacy_inventory',actual)


class UpgradeLatestLayoutTests(UpgradeFromAnOlderReleaseTests):
    source_tag='v0.1.25'

    def test_missing_markdown_dependency_refuses_before_plan_or_source_writes(self):
        root = self.project(self.old, own=True)
        before = files_of(root)
        bin_dir = self.base / 'no-site-packages'
        bin_dir.mkdir()
        python = bin_dir / 'python3'
        python.write_text('#!/bin/sh\nexec /usr/bin/python3 -S "$@"\n')
        python.chmod(0o755)
        env = {**os.environ, 'PATH': f'{bin_dir}:{os.environ["PATH"]}'}
        for arguments in (['--check'], []):
            result = subprocess.run(['bash', str(SCRIPT), *arguments, self.candidate], cwd=root,
                                    capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn('markdown-it-py', result.stderr)
            self.assertNotIn('Applied:', result.stdout)
            self.assertEqual(files_of(root), before)

    def test_previously_generated_project_identity_does_not_collide_with_shared_addition(self):
        old_path = '.agents/tests/test_agent_content.py'
        shared_path = '.agents/tests/shared/test_agent_content.py'
        project_path = '.agents/tests/project/test_agent_content.py'
        identity = 'content-' + hashlib.sha256(old_path.encode()).hexdigest()[:16]
        intermediate = self.base / 'intermediate'
        intermediate.mkdir()
        subprocess.run(['tar', '-x', '-C', str(intermediate)],
                       input=git('archive', 'v0.1.26', cwd=REPOSITORY, raw=True), check=True)
        intermediate_registry = intermediate / REGISTRY
        intermediate_registry.write_text(re.sub(r'^(template:\n  repository: ).*$',
                                                lambda m: m.group(1) + str(self.template),
                                                intermediate_registry.read_text(), count=1, flags=re.M))
        git('init', '-q', cwd=intermediate)
        git('add', '-A', cwd=intermediate)
        git(*IDENTITY, 'commit', '-qm', 'intermediate release', cwd=intermediate)
        git('fetch', '-q', str(intermediate), 'HEAD:refs/tags/v0.1.26', cwd=self.template)
        target_registry = self.template / REGISTRY
        target = catalog.loads(target_registry.read_text())
        target['entries'].append({'id': identity, 'path': shared_path, 'kind': 'code',
                                  'scope': 'shared', 'owner': 'test', 'summary': 'Shared test.',
                                  'status': 'active', 'source': 'unknown', 'updated': 'unknown',
                                  'supersedes': [], 'superseded_by': []})
        shared = self.template / shared_path
        shared.parent.mkdir(parents=True, exist_ok=True)
        shared.write_text('SHARED = True\n')
        target_registry.write_text(catalog.dumps(target))
        catalog.indexes(self.template, target, write=True)
        git('add', '-A', cwd=self.template)
        git(*IDENTITY, 'commit', '-qm', 'shared fixture', cwd=self.template)
        git('tag', '-f', self.candidate, cwd=self.template)
        root = self.project(self.old, own=True)
        registry = root / REGISTRY
        legacy_file = root / old_path
        legacy_file.parent.mkdir(parents=True, exist_ok=True)
        legacy_file.write_text('LOCAL = True\n')
        registry.write_text(registry.read_text() + f'  - path: {old_path}\n    scope: project\n')
        first = subprocess.run(['bash', str(intermediate / '.agents/scripts/shared/upgrade-template.sh'),
                                'v0.1.26'], cwd=root, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        local = catalog.loads(registry.read_text())
        local_file = root / project_path
        self.assertEqual(local_file.read_text(), 'LOCAL = True\n')
        self.assertEqual(next(e for e in local['entries'] if e['path'] == project_path)['id'], identity)
        legacy_entry = next(e for e in local['local_legacy_inventory']['entries'] if e['path'] == old_path)
        owner = next(e for e in local['local_legacy_inventory']['entries'] if e['path'] == '.agents/memory/project/')
        owner['id'] = 'maintainer-explicit-id'
        registry.write_text(catalog.dumps(local))
        before = files_of(root)
        uncertain = subprocess.run(['bash', str(SCRIPT), self.candidate], cwd=root, capture_output=True, text=True)
        self.assertNotEqual(uncertain.returncode, 0)
        self.assertIn('collides with omitted upstream content', uncertain.stdout + uncertain.stderr)
        self.assertEqual(before, files_of(root))
        del owner['id']
        legacy_entry['id'] = identity
        registry.write_text(catalog.dumps(local))
        before = files_of(root)
        conflict = subprocess.run(['bash', str(SCRIPT), self.candidate], cwd=root, capture_output=True, text=True)
        self.assertNotEqual(conflict.returncode, 0)
        self.assertIn('duplicate stable identity after migration', conflict.stdout + conflict.stderr)
        self.assertNotIn('explicit schema 2 -> 2 and identity/path migration', conflict.stdout)
        self.assertEqual(before, files_of(root))
        del legacy_entry['id']
        registry.write_text(catalog.dumps(local))
        result = subprocess.run(['bash', str(SCRIPT), self.candidate], cwd=root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result_data = catalog.loads(registry.read_text())
        entries = {e['path']: e for e in result_data['entries']}
        self.assertEqual(entries[shared_path]['id'], identity)
        self.assertEqual(entries[project_path]['id'], 'local-' + identity)
        self.assertEqual(entries[project_path]['legacy_generated_id'], identity)
        self.assertEqual(local_file.read_text(), 'LOCAL = True\n')
        self.assertEqual((root / shared_path).read_text(), 'SHARED = True\n')
        self.assertFalse(catalog.relationship_errors(result_data['entries']))
        check = subprocess.run(['bash', '.agents/scripts/shared/check-development.sh'], cwd=root,
                               capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        after = files_of(root)
        again = subprocess.run(['bash', str(SCRIPT), self.candidate], cwd=root, capture_output=True, text=True)
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertEqual(after, files_of(root))

    def test_keeps_project_adaptations_optional_rejection_and_retired_history(self):
        root=self.project(self.old,own=True)
        skill='.agents/skills/shared/worktree-lifecycle/SKILL.md'
        section='\n## In this repository\n\nLocal acceptance remains owned by this project.\n'
        (root/skill).write_text((root/skill).read_text()+section)
        (root/'Dockerfile').unlink()
        registry_path=root/REGISTRY
        registry_path.write_text(registry_path.read_text().replace('  - path: Dockerfile\n','  - path: Dockerfile\n    status: rejected\n    adoption: rejected-by-maintainer\n'))
        local_skill=root/'.agents/skills/local-tool/SKILL.md'
        local_skill.parent.mkdir(parents=True);local_skill.write_text('---\nname: local-tool\ndescription: Local project workflow.\n---\n\n# Local tool\n\nUnique project workflow.\n')
        hook=root/'.agents/scripts/setup-project.sh';hook.write_text('#!/bin/sh\n# project-owned setup\n');hook.chmod(0o755)
        retired='  - path: .agents/memory/project/old-decision.md\n    scope: project\n    id: local-retired-decision\n    status: retired\n    source: historical-user-decision\n    updated: unknown\n'
        path=root/REGISTRY
        path.write_text(path.read_text()+retired+'  - path: .agents/skills/local-tool/\n    scope: project\n    kind: skill\n    id: local-tool-stable\n')
        result=subprocess.run(['bash',str(SCRIPT),'--check',self.candidate],cwd=root,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertTrue(hook.exists());self.assertTrue(local_skill.exists())
        before=files_of(root)
        result=subprocess.run(['bash',str(SCRIPT),self.candidate],cwd=root,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertTrue((root/skill).read_text().endswith(section))
        self.assertFalse((root/'Dockerfile').exists())
        self.assertFalse(hook.exists());self.assertFalse(local_skill.exists())
        self.assertEqual((root/'.agents/scripts/project/setup-project.sh').read_bytes(),before['.agents/scripts/setup-project.sh'][1])
        self.assertEqual((root/'.agents/skills/project/local-tool/SKILL.md').read_bytes(),before['.agents/skills/local-tool/SKILL.md'][1])
        data=catalog.loads(path.read_text())
        retired=next(e for e in data['entries'] if e['id']=='local-retired-decision')
        rejected=next(e for e in data['entries'] if e['path']=='Dockerfile')
        self.assertEqual(rejected['status'],'rejected')
        self.assertEqual(rejected['adoption'],'rejected-by-maintainer')
        self.assertEqual(retired['status'],'retired')
        self.assertEqual(retired['source'],'historical-user-decision')
        tool=next(e for e in data['entries'] if e['id']=='local-tool-stable')
        self.assertEqual(tool['path'],'.agents/skills/project/local-tool/')
        self.assertFalse(any(e['scope']=='template' for e in data['entries']))
        check=subprocess.run(['bash','.agents/scripts/shared/check-development.sh'],cwd=root,text=True,capture_output=True)
        self.assertEqual(check.returncode,0,check.stdout+check.stderr)
        after=files_of(root)
        again=subprocess.run(['bash',str(SCRIPT),self.candidate],cwd=root,text=True,capture_output=True)
        self.assertEqual(again.returncode,0,again.stdout+again.stderr)
        self.assertEqual(files_of(root),after)
        self.assertFalse(any(p.startswith('.agents/scripts/') and len(Path(p).parts)==3 and p.endswith('.sh') for p in after))

    def test_many_to_many_content_is_held_for_review_without_deleting_sources(self):
        path=self.template/REGISTRY;data=catalog.loads(path.read_text())
        move=next(m for m in data['migrations'] if m.get('entity')!='registration' and m['from'][0]['path']=='.agents/scripts/diagnose-environment.sh')
        extra=next(e for e in data['entries'] if e['path']=='.agents/scripts/shared/check-development.sh')
        move['to'].append({'id':extra['id'],'path':extra['path']});move['action']='extract'
        path.write_text(catalog.dumps(data))
        git('add',REGISTRY,cwd=self.template)
        git(*IDENTITY,'commit','-qm','many-to-many fixture',cwd=self.template)
        git('tag','-f',self.candidate,cwd=self.template)
        root=self.project(self.old,own=True)
        old=root/'.agents/scripts/diagnose-environment.sh';content=old.read_bytes()
        result=subprocess.run(['bash',str(SCRIPT),self.candidate],cwd=root,text=True,capture_output=True)
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        self.assertIn('all affected files held',result.stdout)
        self.assertEqual(old.read_bytes(),content)
        self.assertFalse((root/'.agents/scripts/shared/diagnose-environment.sh').exists())
        self.assertFalse((root/'.agents/scripts/shared/check-development.sh').exists())
        self.assertIn('version: '+self.old,(root/REGISTRY).read_text())

    def test_conflicting_existing_destination_keeps_both_files(self):
        root=self.project(self.old,own=True)
        old=root/'.agents/scripts/diagnose-environment.sh'
        new=root/'.agents/scripts/shared/diagnose-environment.sh'
        new.parent.mkdir(parents=True);new.write_text('# local destination with unique evidence\n')
        before=old.read_bytes(),new.read_bytes()
        result=subprocess.run(['bash',str(SCRIPT),self.candidate],cwd=root,text=True,capture_output=True)
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        self.assertIn('conflicting existing destination; both files held',result.stdout)
        self.assertEqual((old.read_bytes(),new.read_bytes()),before)
        self.assertIn('version: '+self.old,(root/REGISTRY).read_text())

    def assert_upgrade_check_repeat(self, root):
        result=subprocess.run(['bash',str(SCRIPT),self.candidate],cwd=root,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        checked=subprocess.run(['bash','.agents/scripts/shared/check-development.sh'],cwd=root,text=True,capture_output=True)
        self.assertEqual(checked.returncode,0,checked.stdout+checked.stderr)
        after=files_of(root)
        repeated=subprocess.run(['bash',str(SCRIPT),self.candidate],cwd=root,text=True,capture_output=True)
        self.assertEqual(repeated.returncode,0,repeated.stdout+repeated.stderr)
        self.assertEqual(files_of(root),after)
        return catalog.loads((root/REGISTRY).read_text())

    def test_upgrade_preserves_adopter_stable_id_and_retargets_migration_references(self):
        root=self.project(self.old,own=True)
        path='.agents/skills/shared/worktree-lifecycle/'
        registry=root/REGISTRY;text=registry.read_text();anchor='  - path: '+path+'\n'
        self.assertEqual(text.count(anchor),1)
        registry.write_text(text.replace(anchor,anchor+'    id: adopter-lifecycle-stable\n'))
        upstream=next(e['id'] for e in catalog.loads((self.template/REGISTRY).read_text())['entries'] if e['path']==path)
        note='.agents/memory/project/old-guide.md'
        (root/note).write_text('# Historical guide\n\nUnique evidence now governed by lifecycle skill.\n')
        with registry.open('a') as out:
            out.write('  - path: '+note+'\n    scope: project\n    kind: memory\n    status: superseded\n    superseded_by: ["'+upstream+'"]\n')
        data=self.assert_upgrade_check_repeat(root)
        entry=next(e for e in data['entries'] if e['path']==path)
        self.assertEqual(entry['id'],'adopter-lifecycle-stable')
        refs=[ref for m in data['migrations'] for ref in m['to'] if ref['path'].startswith(path)]
        self.assertTrue(refs)
        self.assertTrue(all(ref['id']==entry['id'] for ref in refs))
        self.assertIn('adopter-lifecycle-stable',str(data['local_legacy_inventory']))
        history=next(e for e in data['entries'] if e['path']==note)
        self.assertEqual(history['superseded_by'],['adopter-lifecycle-stable'])
        self.assertTrue(all(ref['upstream_id']==upstream for ref in refs))

    def test_upgrade_preserves_historical_body_and_resolves_frontmatter_replacement_ids(self):
        root=self.project(self.old,own=True)
        directory=root/'.agents/memory/project'
        bodies={'old-note.md':'# Earlier choice\n\nUnique historical reason and evidence.\n',
                'new-note.md':'# Current choice\n\nNew evidence changes the decision.\n'}
        for name,status,relationship in (('old-note.md','superseded','superseded_by: new-note.md'),('new-note.md','active','supersedes: old-note.md')):
            (directory/name).write_text('---\nname: '+name[:-3]+'\ndate: 2026-09\nsource: recorded-project-decision\nscope: project\nstatus: '+status+'\n'+relationship+'\n---\n\n'+bodies[name])
        data=self.assert_upgrade_check_repeat(root)
        by_name={Path(e['path']).name:e for e in data['entries']}
        old,new=by_name['old-note.md'],by_name['new-note.md']
        self.assertEqual(old['status'],'superseded')
        self.assertEqual(old['superseded_by'],[new['id']])
        self.assertEqual(new['supersedes'],[old['id']])
        self.assertEqual(old['retention'],'historical')
        for name,body in bodies.items():
            text=(directory/name).read_text()
            self.assertTrue(text.endswith(body));self.assertIn('date: 2026-09',text)
            self.assertIn('source: recorded-project-decision',text)
        self.assertIn('old-note.md',(directory/'AGENTS.md').read_text())
        self.assertIn('superseded history',(directory/'AGENTS.md').read_text())

    def test_upgrade_holds_ambiguous_replacement_without_changing_history_or_version(self):
        root=self.project(self.old,own=True)
        directory=root/'.agents/memory/project'
        old=directory/'old-note.md'
        old.write_text('---\nname: old-note\nstatus: superseded\nsuperseded_by: missing-note.md\n---\n\nUnique evidence must not be dropped.\n')
        before=files_of(root)
        result=subprocess.run(['bash',str(SCRIPT),self.candidate],cwd=root,text=True,capture_output=True)
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        self.assertIn('unresolved lifecycle reference',result.stdout)
        self.assertEqual(files_of(root),before)
        self.assertIn('version: '+self.old,(root/REGISTRY).read_text())
        for name in ('first','second'):
            alternative=directory/name/'missing-note.md'
            alternative.parent.mkdir()
            alternative.write_text('# Alternative with independent evidence\n')
        before=files_of(root)
        ambiguous=subprocess.run(['bash',str(SCRIPT),self.candidate],cwd=root,text=True,capture_output=True)
        self.assertEqual(ambiguous.returncode,1,ambiguous.stdout+ambiguous.stderr)
        self.assertIn('2 matching identities',ambiguous.stdout)
        self.assertEqual(files_of(root),before)



if __name__ == "__main__":
    unittest.main()
