"""Exercise public checker failures, real symlink modes and migration coverage."""
from __future__ import annotations
import ast
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'.agents/scripts/shared'))
import content_registry as registry


class DevelopmentContractTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='development-contract-')
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        listed=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).decode().split('\0')
        for name in set(filter(None,listed)):
            source=ROOT/name
            if not (source.exists() or source.is_symlink()):continue
            target=self.root/name;target.parent.mkdir(parents=True,exist_ok=True)
            if source.is_symlink():target.symlink_to(os.readlink(source))
            else:shutil.copy2(source,target)
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        subprocess.run(['git','add','-A'],cwd=self.root,check=True)
        self.path=self.root/'.agents/content-registry.yaml'
        self.data=registry.loads(self.path.read_text())

    def check(self,*args):
        self.path.write_text(registry.dumps(self.data))
        return subprocess.run(['bash','.agents/scripts/shared/check-development.sh',*args],cwd=self.root,text=True,capture_output=True)

    def rejected(self,fragment):
        result=self.check()
        self.assertNotEqual(result.returncode,0,result.stdout)
        self.assertIn(fragment,result.stderr)

    def test_valid_catalog_and_relative_git_symlinks(self):
        result=self.check()
        self.assertEqual(result.returncode,0,result.stderr)
        modes=subprocess.check_output(['git','ls-files','-s'],cwd=self.root,text=True)
        links=[line for line in modes.splitlines() if line.endswith('/CLAUDE.md') or line.endswith('\tCLAUDE.md')]
        self.assertEqual(len(links),20)
        self.assertTrue(all(line.startswith('120000 ') for line in links))

    def test_unregistered_memory_and_project_skill_are_not_covered_by_defaults(self):
        for path in ('.agents/memory/project/new-note.md','.agents/skills/project/new-skill/SKILL.md'):
            file=self.root/path;file.parent.mkdir(parents=True,exist_ok=True);file.write_text('# new\n')
        self.rejected('unregistered: .agents/memory/project/new-note.md')
        self.assertIn('unregistered: .agents/skills/project/new-skill/SKILL.md',self.check().stderr)

    def test_python_package_and_reasoned_naming_exception(self):
        package=self.root/'.agents/scripts/project/my_package';package.mkdir()
        (package/'__init__.py').write_text('')
        (package/'some_module.py').write_text('VALUE = 1\n')
        self.data['entries'].append({'path':'.agents/scripts/project/my_package/','id':'local-python-package','kind':'code','scope':'project','owner':'project','summary':'Python package.','status':'active','source':'fixture','updated':'unknown'})
        self.data['policy']['naming_exceptions'].append({'pattern':'__init__.py','reason':'Python package entrypoint.'})
        result=self.check('--write-indexes');self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(self.check().returncode,0)

    def test_misplaced_shell_and_recursive_shell_failure(self):
        file=self.root/'.agents/scripts/wrong.sh';file.write_text('if then\n')
        self.rejected('misplaced category content')
        nested=self.root/'.agents/scripts/project/nested';nested.mkdir()
        file.rename(nested/'wrong.sh')
        result=subprocess.run(['bash','.agents/scripts/shared/check-shells.sh'],cwd=self.root,text=True,capture_output=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('wrong.sh',result.stderr)

    def test_conflicting_ownership_dangling_entries_and_naming_exceptions(self):
        self.data['entries'].append(copy.deepcopy(self.data['entries'][0]))
        self.data['entries'].append({**self.data['entries'][0],'id':'missing','path':'.agents/memory/project/missing.md'})
        self.data['policy']['naming_exceptions'].append({'pattern':'Bad_Name.md','reason':''})
        result=self.check()
        for fragment in ('duplicate id','conflicting ownership','dangling active entry','naming exception requires'):
            self.assertIn(fragment,result.stderr)
        self.assertNotEqual(result.returncode,0)

    def test_file_symlink_and_git_mode_are_distinct(self):
        file=self.root/'.agents/tests/CLAUDE.md';file.unlink();file.write_text('AGENTS.md')
        self.rejected('bad CLAUDE link')
        subprocess.run(['git','add',str(file)],cwd=self.root,check=True)
        file.unlink();file.symlink_to('AGENTS.md')
        self.rejected('Git mode is not 120000')
        file.unlink();file.symlink_to('../../missing.md')
        self.rejected('bad CLAUDE link')

    def test_replacement_cycles_dangling_and_inactive_chains(self):
        a,b=self.data['entries'][:2]
        a['superseded_by']=[b['id']];b['superseded_by']=[a['id']]
        self.rejected('replacement cycle')
        b['superseded_by']=['missing-id'];self.rejected('dangling replacement')
        b['superseded_by']=[];b['status']='retired';self.rejected('inactive replacement chain')

    def test_index_is_derived_and_stale_index_fails(self):
        entry=next(e for e in self.data['entries'] if e['kind']=='memory')
        entry['summary']='Changed authority summary.'
        self.rejected('stale index')
        result=self.check('--write-indexes');self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(self.check().returncode,0)

    def test_schema_one_gets_explicit_migration_error(self):
        self.data['schema_version']=1
        self.rejected('use the target release upgrade command')

    def test_many_to_many_map_and_complete_old_inventory(self):
        first,second=self.data['migrations'][:2]
        merged={**first,'from':first['from']+second['from'],'to':first['to']+second['to'],'action':'extract'}
        self.data['migrations']=[merged]+self.data['migrations'][2:]
        result=self.check();self.assertEqual(result.returncode,0,result.stderr)
        self.data['migrations'].pop(0)
        self.rejected('unmapped historical path')

    def test_normalized_test_discovery_does_not_shrink(self):
        def names(source):
            tree=ast.parse(source)
            return {c.name+'.'+f.name for c in tree.body if isinstance(c,ast.ClassDef)
                    for f in c.body if isinstance(f,ast.FunctionDef) and f.name.startswith('test_')}
        def flatten(suite):
            for item in suite:
                if isinstance(item,unittest.TestSuite):yield from flatten(item)
                else:yield item.id()
        discovered=set(flatten(unittest.defaultTestLoader.discover(str(ROOT/'.agents/tests/project'),pattern='test_template_*.py')))
        compared=0
        for move in self.data['migrations']:
            if move.get('entity')=='registration':continue
            for old in move['from']:
                if not old['path'].startswith('.agents/tests/test_'):continue
                before=subprocess.check_output(['git','show',move['source_commit']+':'+old['path']],cwd=ROOT,text=True)
                new=move['to'][0]['path']
                self.assertLessEqual(names(before),names((ROOT/new).read_text()),new)
                normalized={Path(new).stem+'.'+name for name in names(before)}
                self.assertLessEqual(normalized,discovered,new)
                compared+=1
        self.assertEqual(compared,9)


if __name__=='__main__':unittest.main()
