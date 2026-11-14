"""Upgrade a project made from an older real release to the release candidate
(this working tree) with the candidate's upgrade-template.sh; the result must
equal a project made from the candidate, except the project's own files."""
from __future__ import annotations

import fnmatch
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[3]
COMMANDS = Path(os.environ.get("TEMPLATE_COMMAND_DIR") or REPOSITORY / ".agents/scripts/shared").resolve()
SCRIPT = COMMANDS / "upgrade-template.sh"
sys.path.insert(0, str(COMMANDS))
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


def drop_obsolete_blocks(registry: Path) -> None:
    """Remove the history blocks a repository kept before the registry recorded
    current state only; the upgrade command does the same."""
    lines = registry.read_text(encoding="utf-8").splitlines(keepends=True)
    kept, skipping = [], False
    for line in lines:
        if re.match(r"^(legacy_inventory|local_legacy_inventory|migrations):", line):
            skipping = True
            continue
        if skipping and line[:1] and not line[0].isspace():
            skipping = False
        if not skipping:
            kept.append(line)
    registry.write_text("".join(kept), encoding="utf-8")


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
        floor = re.search(r"^minimum_upgrade_source: (\S+)", registry, re.M)
        self.floor = floor.group(1) if floor else None
        # Below the declared floor the command refuses the upgrade: those
        # releases predate the current registry shape.
        supported = [tag for tag in tags if self.floor is None or number(tag) >= number(self.floor)]
        if not supported:
            self.skipTest(f"no release at or after the minimum upgrade source {self.floor}"
                          f" can be upgraded to {self.candidate}")
        wanted = (supported[-1] if getattr(self, 'latest_source', False)
                  or self._testMethodName in ('test_relocated_identity_stops_without_writes', 'test_declared_mapping_preserves_location', 'test_bad_mapping_never_changes_checkout', 'test_mapping_content_conflict_is_atomic', 'test_mapped_deletion_preserves_registry_consistency')
                  or self._testMethodName.startswith('test_local_omission')
                  else getattr(self, "source_tag", supported[-2] if len(supported) > 1 else supported[-1]))
        if wanted not in supported:
            self.skipTest(f"{wanted} is older than the minimum upgrade source {self.floor}")
        self.old = wanted

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
        if self._testMethodName.startswith('test_local_omission'):
            dockerfile = self.template/'Dockerfile'
            dockerfile.write_text(dockerfile.read_text() + '# changed upstream\n')
        candidate = getattr(self, 'candidate_' + self._testMethodName[len('test_'):], None)
        if candidate:
            data = catalog.loads((self.template/REGISTRY).read_text())
            candidate(data)
            (self.template/REGISTRY).write_text(catalog.dumps(data))
            catalog.indexes(self.template, data, write=True)
        self.commit(self.candidate)

    def commit(self, tag: str) -> None:
        registry = self.template / REGISTRY
        text = registry.read_text(encoding="utf-8")
        text = re.sub(r"^(template:\n  repository: ).*$", lambda m: m.group(1) + str(self.template), text,
                      count=1, flags=re.M)
        text = re.sub(r"^(template:\n(?:  .*\n)*?  version: )\S+", lambda m: m.group(1) + tag, text,
                      count=1, flags=re.M)
        # The fixture target supports the source it is being upgraded from; the
        # released floor is checked by its own test.
        text = re.sub(r"^(minimum_upgrade_source: )\S+", lambda m: m.group(1) + self.old, text,
                      count=1, flags=re.M)
        registry.write_text(text, encoding="utf-8")
        git("add", "-A", cwd=self.template)
        git(*IDENTITY, "commit", "-qm", tag, cwd=self.template)
        git("tag", tag, cwd=self.template)

    def project(self, tag: str, own: bool, name: str = "") -> Path:
        root = self.base / (name or f"project-{tag}")
        root.mkdir()
        archive = git("archive", tag, cwd=self.template, raw=True)
        subprocess.run(["tar", "-x", "-C", str(root)], input=archive, check=True)
        drop_obsolete_blocks(root / REGISTRY)
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

    def omission_project(self, omitted: dict, live: dict, absent: tuple) -> tuple:
        project=self.project(self.old,own=True)
        registry=project/REGISTRY;data=catalog.loads(registry.read_text())
        for path,reason in omitted.items():
            entry=next(e for e in data['entries'] if e['path']==path)
            if path in live: entry.update(live[path])
            else: data['entries'].remove(entry)
            data['omitted'].append({'id':entry['id'],'path':path,'reason':reason})
        for path in absent: (project/path).unlink()
        registry.write_text(catalog.dumps(data));catalog.indexes(project,data,write=True)
        return project,registry

    def assert_plan_lines(self, project, expected: dict) -> None:
        plan=subprocess.run(['bash',str(SCRIPT),'--check',self.candidate],cwd=project,text=True,capture_output=True)
        self.assertEqual(plan.returncode,0,plan.stdout+plan.stderr)
        for path,line in expected.items():
            mentions=[x.strip() for x in plan.stdout.splitlines() if re.search(r'(^|\s)'+re.escape(path)+r'[\s:]',x)]
            self.assertEqual(mentions,[line],plan.stdout)

    def assert_upgraded_without_duplicates(self, project, registry) -> dict:
        result=subprocess.run(['bash',str(SCRIPT),self.candidate],cwd=project,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        merged=catalog.loads(registry.read_text())
        live={e['path'] for e in merged['entries']}|{e['id'] for e in merged['entries']}
        self.assertFalse([x for x in merged['omitted'] if x['path'] in live or x['id'] in live])
        check=subprocess.run(['bash','.agents/scripts/shared/check-development.sh'],cwd=project,text=True,capture_output=True)
        self.assertEqual(check.returncode,0,check.stdout+check.stderr)
        return merged

    def test_local_omissions_are_kept_out_or_adopted_never_both(self) -> None:
        reasons={'Dockerfile':'This project does not adopt the container skeleton.',
                 'install.sh':'Left out once; the project now ships its own installer.'}
        project,registry=self.omission_project(reasons,{},('Dockerfile',))
        self.assert_plan_lines(project,{'Dockerfile':'kept out: Dockerfile (omitted locally)',
                                        'install.sh':'adopted: install.sh (omission dropped; file present)'})
        merged=self.assert_upgraded_without_duplicates(project,registry)
        self.assertFalse((project/'Dockerfile').exists())
        omitted={x['path']:x for x in merged['omitted']}
        self.assertEqual(omitted['Dockerfile']['reason'],reasons['Dockerfile'])
        self.assertNotIn('install.sh',omitted)
        self.assertIn('install.sh',{e['path'] for e in merged['entries']})

    def test_local_omission_with_a_live_duplicate_is_cleaned_up(self) -> None:
        reason='Template-only content this project does not adopt.'
        project,registry=self.omission_project({'USER.md':reason},{'USER.md':{}},('USER.md',))
        broken=subprocess.run(['bash','.agents/scripts/shared/check-development.sh'],cwd=project,text=True,capture_output=True)
        self.assertIn('dangling active entry: USER.md',broken.stdout+broken.stderr)
        self.assert_plan_lines(project,{'USER.md':'kept out: USER.md (omitted locally)'})
        merged=self.assert_upgraded_without_duplicates(project,registry)
        self.assertNotIn('USER.md',{e['path'] for e in merged['entries']})
        self.assertEqual([x['reason'] for x in merged['omitted'] if x['path']=='USER.md'],[reason])
        self.assertFalse((project/'USER.md').exists())

    def test_local_omission_beside_a_local_lifecycle_is_dropped(self) -> None:
        reason='Rejected container skeleton.'
        lifecycle={'status':'rejected','adoption':'rejected-by-maintainer'}
        project,registry=self.omission_project({'Dockerfile':reason},{'Dockerfile':lifecycle},('Dockerfile',))
        self.assert_plan_lines(project,{'Dockerfile':f'kept rejected: Dockerfile (redundant omission dropped: {reason})'})
        merged=self.assert_upgraded_without_duplicates(project,registry)
        entry=next(e for e in merged['entries'] if e['path']=='Dockerfile')
        self.assertEqual((entry['status'],entry['adoption']),('rejected','rejected-by-maintainer'))
        self.assertNotIn('Dockerfile',{x['path'] for x in merged['omitted']})
        self.assertFalse((project/'Dockerfile').exists())

    def test_local_omission_beside_a_retired_present_file_is_refused(self) -> None:
        project,registry=self.omission_project({'Dockerfile':'Retired skeleton.'},{'Dockerfile':{'status':'retired'}},())
        before=files_of(project)
        result=subprocess.run(['bash',str(SCRIPT),self.candidate],cwd=project,text=True,capture_output=True)
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        self.assertIn('Dockerfile: local status retired and omitted, but the file is present; reconcile by hand',result.stdout)
        self.assertEqual(files_of(project),before)
        self.assertIn('version: '+self.old,registry.read_text())

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

    def test_declared_minimum_source_refuses_an_older_repository(self) -> None:
        root = self.project(self.old, own=True)
        newer = 'v0.1.99'
        registry = self.template / REGISTRY
        registry.write_text(re.sub(r"^minimum_upgrade_source: \S+", f"minimum_upgrade_source: {newer}",
                                   registry.read_text(), count=1, flags=re.M), encoding='utf-8')
        git('add', REGISTRY, cwd=self.template)
        git(*IDENTITY, 'commit', '-qm', 'raise the floor', cwd=self.template)
        git('tag', newer, cwd=self.template)
        before = files_of(root)
        result = subprocess.run(['bash', str(SCRIPT), newer], cwd=root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn(f'{newer} supports upgrades from {newer} and later', result.stderr)
        self.assertIn('template-adoption', result.stderr)
        self.assertEqual(files_of(root), before)

    def test_obsolete_history_blocks_are_removed_and_reported(self) -> None:
        root = self.project(self.old, own=True)
        registry = root / REGISTRY
        blocks = ('legacy_inventory: {\n    "entries": []\n  }\n'
                  'local_legacy_inventory: {"version": "v0.1.1", "entries": []}\n'
                  'migrations: [\n  ]\n')
        registry.write_text(registry.read_text().replace('entries:\n', blocks + 'entries:\n', 1))
        self.assertIn('legacy_inventory:', registry.read_text())
        result = subprocess.run(['bash', str(SCRIPT), self.candidate], cwd=root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('removed legacy_inventory, local_legacy_inventory, migrations; the history stays in Git',
                      result.stdout)
        merged = catalog.loads(registry.read_text())
        for key in ('legacy_inventory', 'local_legacy_inventory', 'migrations'):
            self.assertNotIn(key, merged)
        checked = subprocess.run(['bash', '.agents/scripts/shared/check-development.sh'], cwd=root,
                                 text=True, capture_output=True)
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

    def candidate_a_removed_shared_package_leaves_nothing_behind(self, data):
        package = '.agents/skills/shared/template-feedback/'
        for entry in [e for e in data['entries'] if e['path'] == package]:
            data['entries'].remove(entry)
            data.setdefault('omitted', []).append(
                {'id': entry['id'], 'path': entry['path'], 'reason': 'Removed upstream.'})
        shutil.rmtree(self.template / package)

    def test_a_removed_shared_package_leaves_nothing_behind(self) -> None:
        root = self.project(self.old, own=True)
        package = '.agents/skills/shared/template-feedback'
        self.assertTrue((root / package).is_dir())
        result = subprocess.run(['bash', str(SCRIPT), self.candidate], cwd=root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((root / package).exists(), result.stdout)
        self.assertIn(f'{package}/SKILL.md: removed', result.stdout)
        again = subprocess.run(['bash', str(SCRIPT), self.candidate], cwd=root, text=True, capture_output=True)
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        checked = subprocess.run(['bash', '.agents/scripts/shared/check-development.sh'], cwd=root,
                                 text=True, capture_output=True)
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

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


def unit(path: str, identity: str, kind: str, scope: str = 'project', **fields) -> dict:
    return {'path': path, 'id': identity, 'kind': kind, 'scope': scope, 'owner': 'project-maintainers',
            'summary': 'Fixture unit.', 'status': 'active', 'source': 'unknown', 'updated': 'unknown',
            'supersedes': [], 'superseded_by': [], **fields}


def migration(action: str, sources: list, destinations: list) -> dict:
    return {'from': sources, 'to': destinations, 'action': action, 'reason': 'Fixture migration.',
            'source_commit': 'fixture', 'verification': 'upgrade regression'}


class TemplateCommandSyncTests(unittest.TestCase):
    """Generic fixes first carried by a derived template, from the latest release to the candidate."""
    latest_source = True
    setUp = UpgradeFromAnOlderReleaseTests.setUp
    commit = UpgradeFromAnOlderReleaseTests.commit
    project = UpgradeFromAnOlderReleaseTests.project
    omission_project = UpgradeFromAnOlderReleaseTests.omission_project
    assert_plan_lines = UpgradeFromAnOlderReleaseTests.assert_plan_lines
    assert_upgraded_without_duplicates = UpgradeFromAnOlderReleaseTests.assert_upgraded_without_duplicates

    def run_command(self, root, *arguments):
        return subprocess.run(['bash', str(SCRIPT), *arguments, self.candidate], cwd=root, text=True, capture_output=True)

    def check(self, root):
        return subprocess.run(['bash', '.agents/scripts/shared/check-development.sh'], cwd=root, text=True, capture_output=True)

    def save(self, root, data):
        (root/REGISTRY).write_text(catalog.dumps(data))
        catalog.indexes(root, data, write=True)

    def derived(self, name, upstream=True, harvest=True):
        root = self.project(self.old, own=True, name=name)
        data = catalog.loads((root/REGISTRY).read_text())
        if upstream:
            data['template'] = {'repository': 'https://example.invalid/derived-template', 'version': 'v0.0.1',
                                'upstream': {'repository': str(self.template), 'version': self.old}}
        maintenance = '.agents/memory/project/derived-maintenance.md'
        (root/maintenance).write_text('# Derived maintenance\n\nHow this derived template is released.\n')
        data['entries'].append(unit(maintenance, 'derived-maintenance', 'memory', 'template'))
        if not harvest:
            self.save(root, data)
            return root, None
        harvest = next(e for e in catalog.loads((self.template/REGISTRY).read_text())['entries']
                       if e['path'] == '.agents/memory/project/harvest-renamed.md')
        harvest = {**harvest, 'path': '.agents/memory/project/harvest-decisions.md'}
        (root/harvest['path']).write_text('# Derived harvest decisions\n')
        data['entries'].append(unit(harvest['path'], harvest['id'], 'memory', 'template'))
        data['omitted'] = [x for x in data['omitted'] if x['id'] != harvest['id']]
        references = root/'.agents/references/sources.md'
        references.parent.mkdir()
        references.write_text('# Sources\n')
        data['entries'].append(unit('.agents/references/sources.md', 'derived-sources', 'document'))
        data['policy']['root_files'].append('references')
        self.save(root, data)
        return root, harvest['id']

    def test_a_project_without_upstream_still_drops_template_entries(self):
        root, _ = self.derived('plain', upstream=False, harvest=False)
        result = self.run_command(root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        after = catalog.loads((root/REGISTRY).read_text())
        self.assertFalse([e for e in after['entries'] if e['scope'] == 'template'])

    def test_optional_entry_without_a_file_becomes_an_omission(self):
        root = self.project(self.old, own=True)
        (root/'install.sh').unlink()
        self.assert_plan_lines(root, {'install.sh': 'omitted: install.sh (optional entry without a file recorded as an omission)'})
        merged = self.assert_upgraded_without_duplicates(root, root/REGISTRY)
        self.assertNotIn('install.sh', {e['path'] for e in merged['entries']})
        self.assertIn('install.sh', {x['path'] for x in merged['omitted'] if x['reason']})
        self.assertFalse((root/'install.sh').exists())

    def test_project_release_notes_at_a_template_only_path(self):
        root = self.project(self.old, own=True)
        data = catalog.loads((root/REGISTRY).read_text())
        notes = next(x for x in data['omitted'] if x['path'] == 'RELEASE_NOTES.md')
        data['entries'].append(unit('RELEASE_NOTES.md', notes['id'], 'document'))
        self.save(root, data)
        candidate_checker = subprocess.run([sys.executable, str(COMMANDS/'content_registry.py'), '--root', str(root)],
                                           text=True, capture_output=True)
        self.assertIn('omitted and registered: RELEASE_NOTES.md', candidate_checker.stderr)
        plan = self.run_command(root, '--check')
        self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
        self.assertIn('  project-owned: RELEASE_NOTES.md (template-only omission dropped; file present)\n', plan.stdout)
        merged = self.assert_upgraded_without_duplicates(root, root/REGISTRY)
        self.assertEqual(next(e for e in merged['entries'] if e['path'] == 'RELEASE_NOTES.md')['id'], notes['id'])
        self.assertEqual((root/'RELEASE_NOTES.md').read_text(), OWN_FILES['RELEASE_NOTES.md'])


TARGET_REASON = 'Optional content left out here (recorded from an optional entry without a file).'


def target_omits_dockerfile(self, data):
    entry = next(e for e in data['entries'] if e['path'] == 'Dockerfile')
    data['entries'].remove(entry)
    data.setdefault('omitted', []).append({'id': entry['id'], 'path': 'Dockerfile', 'reason': TARGET_REASON})
    (self.template/'Dockerfile').unlink()


class TargetOmissionTests(unittest.TestCase):
    """A target registry that records its own omissions, as a derived template does."""
    latest_source = True
    setUp = UpgradeFromAnOlderReleaseTests.setUp
    commit = UpgradeFromAnOlderReleaseTests.commit
    project = UpgradeFromAnOlderReleaseTests.project
    assert_plan_lines = UpgradeFromAnOlderReleaseTests.assert_plan_lines
    assert_upgraded_without_duplicates = UpgradeFromAnOlderReleaseTests.assert_upgraded_without_duplicates
    candidate_target_omission_with_a_local_omission_keeps_the_local_reason = target_omits_dockerfile
    candidate_target_omission_with_a_local_duplicate_entry = target_omits_dockerfile
    candidate_target_omission_without_a_local_record = target_omits_dockerfile
    candidate_target_omission_with_a_stale_local_entry = target_omits_dockerfile

    def downstream(self, entry: bool, reason: str | None):
        root = self.project(self.old, own=True)
        registry = root/REGISTRY
        data = catalog.loads(registry.read_text())
        dockerfile = next(e for e in data['entries'] if e['path'] == 'Dockerfile')
        if not entry:
            data['entries'].remove(dockerfile)
        if reason:
            data['omitted'].append({'id': dockerfile['id'], 'path': 'Dockerfile', 'reason': reason})
        (root/'Dockerfile').unlink()
        registry.write_text(catalog.dumps(data))
        catalog.indexes(root, data, write=True)
        return root, registry

    def assert_single_omission(self, root, registry, reason):
        merged = self.assert_upgraded_without_duplicates(root, registry)
        self.assertEqual([x['reason'] for x in merged['omitted'] if x['path'] == 'Dockerfile'], [reason])
        self.assertNotIn('Dockerfile', {e['path'] for e in merged['entries']})
        self.assertFalse((root/'Dockerfile').exists())
        after = files_of(root)
        again = subprocess.run(['bash', str(SCRIPT), self.candidate], cwd=root, text=True, capture_output=True)
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertEqual(files_of(root), after)

    def test_target_omission_with_a_local_omission_keeps_the_local_reason(self):
        root, registry = self.downstream(entry=False, reason='This paper ships no container.')
        self.assert_single_omission(root, registry, 'This paper ships no container.')

    def test_target_omission_with_a_local_duplicate_entry(self):
        root, registry = self.downstream(entry=True, reason='This paper ships no container.')
        self.assert_plan_lines(root, {'Dockerfile': 'kept out: Dockerfile (omitted locally)'})
        self.assert_single_omission(root, registry, 'This paper ships no container.')

    def test_target_omission_without_a_local_record(self):
        root, registry = self.downstream(entry=False, reason=None)
        self.assert_single_omission(root, registry, TARGET_REASON)

    def test_target_omission_with_a_stale_local_entry(self):
        root, registry = self.downstream(entry=True, reason=None)
        self.assert_plan_lines(root, {'Dockerfile': f'kept out: Dockerfile (omitted in {self.candidate})'})
        self.assert_single_omission(root, registry, TARGET_REASON)


class UpgradeLatestLayoutTests(UpgradeFromAnOlderReleaseTests):

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

    def test_keeps_project_adaptations_optional_rejection_and_retired_history(self):
        root=self.project(self.old,own=True)
        skill='.agents/skills/shared/worktree-lifecycle/SKILL.md'
        section='\n## In this repository\n\nLocal acceptance remains owned by this project.\n'
        (root/skill).write_text((root/skill).read_text()+section)
        (root/'Dockerfile').unlink()
        registry_path=root/REGISTRY
        data=catalog.loads(registry_path.read_text())
        rejected=next(e for e in data['entries'] if e['path']=='Dockerfile')
        rejected['status']='rejected';rejected['adoption']='rejected-by-maintainer'
        local_skill=root/'.agents/skills/local-tool/SKILL.md'
        local_skill.parent.mkdir(parents=True);local_skill.write_text('---\nname: local-tool\ndescription: Local project workflow.\n---\n\n# Local tool\n\nUnique project workflow.\n')
        hook=root/'.agents/scripts/setup-project.sh';hook.write_text('#!/bin/sh\n# project-owned setup\n');hook.chmod(0o755)
        data['entries'].append(unit('.agents/memory/project/old-decision.md','local-retired-decision','memory',
                                    status='retired',source='historical-user-decision'))
        data['entries'].append(unit('.agents/skills/local-tool/','local-tool-stable','skill'))
        path=root/REGISTRY
        registry_path.write_text(catalog.dumps(data))
        catalog.indexes(root,data,write=True)
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
