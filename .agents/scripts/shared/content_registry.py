"""Canonical development registry format, validation and generated routing indexes.

This is deliberately a documented YAML subset, not a permissive YAML parser.
JSON flow values keep nested provenance unambiguous without dependencies.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import unicodedata
from urllib.parse import unquote, urlsplit
from pathlib import Path, PurePosixPath

sys.dont_write_bytecode = True

CATEGORIES = ('execution', 'tests', 'memory', 'knowledge', 'skills', 'scripts')
SCOPES = {'shared', 'shared_with_adaptation', 'project', 'template'}
STATUSES = {'active', 'superseded', 'retired', 'rejected'}
BEGIN = '<!-- registry-index:start -->'
END = '<!-- registry-index:end -->'


class RegistryError(ValueError):
    pass


def value(text):
    text = text.strip()
    if not text:
        return {}
    if text[0] in '[{"' or text in ('true', 'false', 'null') or re.fullmatch(r'-?\d+', text):
        try:
            return json.loads(text)
        except ValueError as exc:
            raise RegistryError(f'invalid JSON flow value: {text[:80]}') from exc
    if text.startswith(('!', '&', '*', '|', '>', "'")) or ' #' in text:
        raise RegistryError(f'unsupported YAML syntax; use a JSON string: {text[:80]}')
    return text


def loads(text):
    result = {}
    stack = [(-1, result)]
    lines=iter(enumerate(text.splitlines(),1))
    for number, line in lines:
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        match = re.fullmatch(r'( *)(- )?([a-zA-Z_][\w-]*):(?: (.*))?', line)
        if not match:
            raise RegistryError(f'line {number}: expected canonical YAML mapping/entry')
        indent, item, key, raw = match.groups()
        if raw and raw.lstrip().startswith(('[','{')):
            while True:
                try:
                    json.loads(raw)
                    break
                except json.JSONDecodeError:
                    try: _,following=next(lines)
                    except StopIteration: raise RegistryError(f'line {number}: unfinished JSON flow value')
                    raw+='\n'+following
        level = len(indent)
        if item:
            if level != 2 or key != 'path' or not isinstance(result.get('entries'), list):
                raise RegistryError(f'line {number}: entries must start with two-space - path:')
            entry = {'path': value(raw or '')}
            result['entries'].append(entry)
            stack = [(-1, result), (2, entry)]
            continue
        while stack[-1][0] >= level:
            stack.pop()
        parent = stack[-1][1]
        if key in parent:
            raise RegistryError(f'line {number}: duplicate key {key}')
        data = [] if key == 'entries' and level == 0 and not raw else value(raw or '')
        parent[key] = data
        if isinstance(data, dict) and not raw:
            stack.append((level, data))
    return result


def scalar(data):
    if isinstance(data, str) and re.fullmatch(r'[A-Za-z0-9_./*:-]+', data):
        return data
    return json.dumps(data, ensure_ascii=False)


def dumps(data):
    lines = []
    def mapping(record, indent):
        for key, val in record.items():
            if isinstance(val, dict):
                lines.append(' ' * indent + key + ':')
                mapping(val, indent + 2)
            else:
                lines.append(' ' * indent + key + ': ' + scalar(val))
    for key, val in data.items():
        if key == 'entries':
            lines.append('entries:')
            for entry in val:
                ordered = {'path': entry['path'], **entry}
                for index, (name, content) in enumerate(ordered.items()):
                    lines.append(('  - ' if index == 0 else '    ') + name + ': ' + scalar(content))
        elif key in ('template', 'writing'):
            lines.append(key + ':')
            mapping(val, 2)
        else:
            if isinstance(val,(dict,list)):
                formatted=json.dumps(val,ensure_ascii=False,indent=2).splitlines()
                lines.append(key+': '+formatted[0])
                lines.extend('  '+line for line in formatted[1:])
            else:
                lines.append(key + ': ' + scalar(val))
    return '\n'.join(lines) + '\n'


def safe_path(path):
    return isinstance(path, str) and path not in ('', '.', '/') and not path.startswith('/') and '\\' not in path and all(x not in ('', '.', '..') for x in path.rstrip('/').split('/'))


def rank(path, pattern):
    if pattern.endswith('/'):
        return (1, len(pattern)) if path.startswith(pattern) else None
    if any(c in pattern for c in '*?['):
        # glob * cannot cross a directory; ** can.
        expression = ''.join('(?:.*/)?' if x == '**/' else '[^/]*' if x == '*' else '[^/]' if x == '?' else re.escape(x)
                             for x in re.split(r'(\*\*/|\*|\?)', pattern))
        return (2, len(pattern)) if re.fullmatch(expression, path) else None
    return (3, len(pattern)) if path == pattern else None


def resolve(path, entries):
    matches = [(rank(path, e['path']), e) for e in entries if rank(path, e['path'])]
    if not matches:
        raise RegistryError(f'unregistered: {path}')
    best = max(x[0] for x in matches)
    winners = [e for r, e in matches if r == best]
    if len(winners) != 1:
        raise RegistryError(f'conflicting ownership: {path}: {[e.get("id") for e in winners]}')
    return winners[0]


def git_files(root):
    output = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=root)
    return sorted(set(x for x in output.decode().split('\0') if x))


def skill_frontmatter_errors(root, files, entries):
    try:
        import yaml
    except ImportError:
        return ['skill frontmatter validation requires PyYAML; install the development dependency']
    class UniqueLoader(yaml.SafeLoader):
        pass
    def unique_mapping(loader, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in result:
                raise ValueError(f'duplicate YAML key: {key}')
            result[key] = loader.construct_object(value_node, deep=deep)
        return result
    UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)
    errors = []
    for path in files:
        if not path.endswith('/SKILL.md'):
            continue
        try:
            entry = resolve(path, entries)
        except RegistryError:
            continue  # ownership validation reports this separately
        if entry.get('kind') != 'skill':
            continue
        try:
            text = (root/path).read_text(encoding='utf-8')
            match = re.match(r'\A---\s*\n(.*?)\n---\s*(?:\n|\Z)', text, re.S)
            if not match:
                raise ValueError('missing YAML frontmatter delimiters')
            front = yaml.load(match.group(1), Loader=UniqueLoader)
            if not isinstance(front, dict):
                raise ValueError('frontmatter must be a mapping')
            for field in ('name', 'description'):
                if not isinstance(front.get(field), str) or not front[field].strip():
                    raise ValueError(f'{field} must be a nonempty string')
            if front['name'] != Path(path).parent.name:
                raise ValueError('name must match the skill directory')
        except (ValueError, OSError, UnicodeError, yaml.YAMLError) as exc:
            errors.append(f'invalid skill frontmatter: {path}: {exc}')
    return errors


def markdown_link_errors(root, files):
    try:
        from markdown_it import MarkdownIt
    except ImportError:
        return ['Markdown link validation requires markdown-it-py; install the development dependency']
    parser = MarkdownIt('commonmark')
    errors = []
    headings = {}
    def anchors(path):
        if path in headings:
            return headings[path]
        seen, result = {}, set()
        tokens = parser.parse(path.read_text(encoding='utf-8'))
        for index, token in enumerate(tokens):
            if token.type != 'heading_open':
                continue
            inline = tokens[index + 1]
            label = ''.join(child.content for child in inline.children or [] if child.type in ('text', 'code_inline'))
            slug = ''.join(c for c in label.lower() if c in ' -_' or unicodedata.category(c)[0] in ('L', 'N', 'M')).replace(' ', '-')
            count = seen.get(slug, 0); seen[slug] = count + 1
            result.add(slug if not count else f'{slug}-{count}')
        headings[path] = result
        return result
    for name in files:
        if not name.startswith('.agents/') or not name.endswith('.md') or name.endswith('/CLAUDE.md'):
            continue
        source = root/name
        if not source.is_file():
            continue
        for token in parser.parse(source.read_text(encoding='utf-8')):
            for child in token.children or []:
                if child.type not in ('link_open', 'image'):
                    continue
                href = child.attrGet('href' if child.type == 'link_open' else 'src') or ''
                parsed = urlsplit(href)
                if parsed.scheme or parsed.netloc or href.startswith('/'):
                    continue
                target = (source.parent/unquote(parsed.path)).resolve() if parsed.path else source.resolve()
                if not target.exists():
                    errors.append(f'broken Markdown link: {name}: {href}')
                elif parsed.fragment and target.is_file() and target.suffix.lower() == '.md' and unquote(parsed.fragment) not in anchors(target):
                    errors.append(f'broken Markdown anchor: {name}: {href}')
    return errors


def generated_index(root, directory, entries):
    rows = []
    prefix = directory + '/'
    for e in entries:
        p = e['path']
        if (e['status'] != 'active' and not historical_body(e)) or not p.startswith(prefix) or e['kind'] in ('governance', 'symlink-index'):
            continue
        rest = p[len(prefix):].rstrip('/')
        if not rest or not (root / p).exists():
            continue
        if '/' in rest and not (e['kind'] in ('memory', 'knowledge', 'document') and directory.split('/')[1] in ('memory', 'knowledge')):
            continue
        target = rest + '/SKILL.md' if e['kind'] == 'skill' else rest
        label = f" ({e['status']} history)" if historical_body(e) else ""
        rows.append(f'- [{rest}]({target}){label} — {e["summary"]}')
    return BEGIN + '\n' + '\n'.join(sorted(rows)) + '\n' + END


def indexes(root, data, write=False):
    errors = []
    for category in CATEGORIES:
        for group in ('shared', 'project'):
            directory = f'.agents/{category}/{group}'
            file = root / directory / 'AGENTS.md'
            if not file.is_file():
                continue
            text = file.read_text()
            wanted = generated_index(root, directory, data['entries'])
            expression = re.compile(re.escape(BEGIN) + '.*?' + re.escape(END), re.S)
            found = expression.findall(text)
            if found == [wanted]:
                continue
            if not write:
                errors.append(f'stale index: {file.relative_to(root)}; run check-development.sh --write-indexes')
            else:
                if len(found) > 1:
                    raise RegistryError(f'duplicate generated index markers: {file}')
                file.write_text(expression.sub(lambda _: wanted, text) if found else text.rstrip() + '\n\n' + wanted + '\n')
    return errors


def historical_body(entry):
    return (entry.get('kind') in ('memory', 'knowledge')
            and entry.get('status') in ('superseded', 'retired')
            and entry.get('retention') == 'historical'
            and isinstance(entry.get('retention_reason'), str)
            and bool(entry['retention_reason'].strip()))


def relationship_errors(entries):
    errors = []
    fail = errors.append
    ids = {entry['id']: entry for entry in entries}
    if len(ids) != len(entries):
        duplicates = sorted({entry['id'] for entry in entries
                             if sum(other['id'] == entry['id'] for other in entries) > 1})
        fail('duplicate stable identity after migration: ' + ', '.join(
            f"{eid} ({', '.join(e['path'] for e in entries if e['id'] == eid)})"
            for eid in duplicates))
    # One canonical old -> replacement graph, including reciprocal declarations.
    graph = {key: set() for key in ids}
    for eid, e in ids.items():
        for key, reverse in (('superseded_by', False), ('supersedes', True)):
            for other in e.get(key, []) if isinstance(e.get(key, []), list) else []:
                if other not in ids:
                    fail(f'dangling replacement: {eid} -> {other}')
                else:
                    graph[other if reverse else eid].add(eid if reverse else other)
        if e.get('status') == 'superseded' and not e.get('superseded_by'):
            fail(f'superseded entry without replacement: {eid}')
    done, visiting = set(), set()
    def visit(eid):
        if eid in visiting:
            fail(f'replacement cycle: {eid}')
            return
        if eid in done:
            return
        visiting.add(eid)
        for other in graph[eid]:
            visit(other)
        if graph[eid] and all(ids[x].get('status') in ('retired','rejected') for x in graph[eid]):
            fail(f'inactive replacement chain: {eid}')
        visiting.remove(eid)
        done.add(eid)
    for eid in graph:
        visit(eid)
    return errors


def omission_errors(data):
    errors = []
    fail = errors.append
    omitted = data.get('omitted', [])
    if not isinstance(omitted, list):
        return ['omitted must be a list of id/path/reason records']
    registered = {e.get('id'): e for e in data.get('entries', [])}
    seen = {}
    for record in omitted:
        if not isinstance(record, dict):
            fail(f'invalid omission: {record!r}; use an id/path/reason record')
            continue
        eid, path, reason = record.get('id'), record.get('path'), record.get('reason')
        if not eid or not safe_path(path) or not isinstance(reason, str) or not reason.strip() or set(record) - {'id', 'path', 'reason'}:
            fail(f'invalid omission: {path or eid}; requires only id, path and a nonempty reason')
        for key in (eid, path):
            if key and key in seen and seen[key] is not record:
                fail(f'duplicate omission: {key}')
            seen.setdefault(key, record)
        entry = registered.get(eid)
        if entry:
            fail(f'omitted and registered: {path} ({eid}) is also entry {entry.get("path")} ({entry.get("id")}); '
                 'run the target release upgrade command or keep one record')
    return errors


OBSOLETE_BLOCKS = ('legacy_inventory', 'local_legacy_inventory', 'migrations')


def validate(root, data):
    errors = []
    fail = errors.append
    if data.get('schema_version') != 2:
        return ['unsupported registry schema; schema 1 requires the target release upgrade command and migration map']
    found = [key for key in OBSOLETE_BLOCKS if key in data]
    if found:
        return [f"obsolete registry history blocks: {', '.join(found)}; the registry records current state only."
                ' Remove them and keep the history in Git (the upgrade command does this), or adopt the template again'
                ' (template-adoption)']
    entries = data.get('entries', [])
    ids = {}
    paths = {}
    for e in entries:
        for key in ('id', 'path', 'kind', 'scope', 'owner', 'summary', 'status', 'source', 'updated'):
            if not e.get(key):
                fail(f'entry {e.get("path")}: missing {key}; use unknown for unavailable history')
        eid, path = e.get('id'), e.get('path', '')
        if eid in ids:
            fail(f'duplicate id: {eid}')
        ids[eid] = e
        if path in paths:
            fail(f'conflicting ownership: duplicate path {path}')
        paths[path] = e
        if not safe_path(path):
            fail(f'unsafe registry path: {path}')
        if e.get('scope') not in SCOPES or e.get('status') not in STATUSES:
            fail(f'invalid scope/status: {path}')
        if e.get('scope') == 'shared_with_adaptation' and not e.get('adaptation'):
            fail(f'missing adaptation: {path}')
        if e.get('kind') == 'knowledge' and not e.get('refresh_after'):
            fail(f'missing refresh_after: {path}')
        if e.get('updated') != 'unknown' and not re.fullmatch(r'\d{4}-\d{2}(?:-\d{2})?', str(e.get('updated'))):
            fail(f'invalid updated (do not invent a day): {path}')
        if e.get('retention') and not historical_body(e):
            fail(f'invalid historical retention: {path}')
        for key in ('supersedes', 'superseded_by'):
            if not isinstance(e.get(key, []), list):
                fail(f'{key} must contain stable IDs: {path}')
    errors.extend(relationship_errors(entries))
    errors.extend(omission_errors(data))
    policy = data.get('policy', {})
    exceptions = policy.get('naming_exceptions', [])
    for exception in exceptions:
        if not exception.get('pattern') or not exception.get('reason', '').strip():
            fail('naming exception requires pattern and reason')
    files = git_files(root)
    # Layout checks must use the same Git-visible set as ownership checks.
    # A tracked file remains visible even if an ignore rule also matches it.
    def visible(path):
        relative = path.relative_to(root).as_posix()
        return any(p == relative or p.startswith(relative + '/') for p in files)
    managed = [p for p in files if any(p.startswith(x) for x in data.get('managed', ['.agents/'])) or any(rank(p,e.get('path','')) for e in entries)]
    live = [p for p in managed if (root/p).exists() or (root/p).is_symlink()]
    errors.extend(skill_frontmatter_errors(root, live, entries))
    errors.extend(markdown_link_errors(root, live))
    for e in entries:
        if e.get('status') == 'active' and not any(rank(p,e['path']) for p in live) and not e.get('optional'):
            fail(f'dangling active entry: {e["path"]}')
    for p in live:
        try:
            entry = resolve(p, entries)
        except RegistryError as exc:
            fail(str(exc)); continue
        if entry['status'] != 'active' and not historical_body(entry):
            fail(f'inactive content present: {p}')
        if entry['path'] != p and entry['kind'] not in ('skill', 'code', 'governance'):
            fail(f'independent content needs its own entry: {p}')
        parts = PurePosixPath(p).parts
        if len(parts)>3 and parts[0]=='.agents' and parts[1] in CATEGORIES and parts[2]=='shared' and entry['scope'] in ('template','project'):
            fail(f'non-reusable content misplaced in shared: {p}')
        for position,name in enumerate(parts):
            if name == '.agents' or any(fnmatch.fnmatchcase(name, x.get('pattern','')) and x.get('reason') for x in exceptions):
                continue
            stem = name.rsplit('.',1)[0] if '.' in name else name
            python_name=name.endswith('.py') or (root/Path(*parts[:position+1])/'__init__.py').is_file() or (position == len(parts) - 1 and entry.get('language')=='python' and entry['kind']=='code')
            pattern = r'[a-z][a-z0-9_]*' if python_name else r'[a-z0-9]+(?:-[a-z0-9]+)*'
            if not re.fullmatch(pattern, stem):
                fail(f'naming violation: {p} ({name}); register a reasoned exception')
        if (p.endswith('.py') and '/tests/' in p and not PurePosixPath(p).name.startswith('test_')
                and PurePosixPath(p).name != '__init__.py'
                and not any(fnmatch.fnmatchcase(PurePosixPath(p).name, x.get('pattern','')) and x.get('reason') for x in exceptions)):
            fail(f'test module needs test_ prefix: {p}')
        if p.endswith('CLAUDE.md'):
            file = root/p
            if not file.is_symlink() or os.readlink(file) != 'AGENTS.md' or not file.exists():
                fail(f'bad CLAUDE link: {p}; expected relative symlink to same-directory AGENTS.md')
            staged = subprocess.check_output(['git','ls-files','-s','--',p],cwd=root,text=True)
            if staged and staged.split()[0] != '120000':
                fail(f'CLAUDE Git mode is not 120000: {p}')
        if entry['kind'] in ('memory','knowledge') and p.endswith('.md'):
            text=(root/p).read_text()
            front=text.split('---',2)[1] if text.startswith('---\n') and text.count('---')>=2 else ''
            if re.search(r'^(scope|status|supersedes|superseded_by|refresh_after):',front,re.M):
                fail(f'duplicate registry metadata in frontmatter: {p}')
    for category in CATEGORIES:
        base=root/'.agents'/category
        for group in ('', 'shared', 'project'):
            for file in ('AGENTS.md','CLAUDE.md'):
                path=base/group/file
                if not path.exists():fail(f'missing governance: {path.relative_to(root)}')
        for child in base.iterdir() if base.exists() else []:
            if visible(child) and child.name not in ('shared','project','AGENTS.md','CLAUDE.md',*policy.get('category_files',{}).get(category,[])):
                fail(f'misplaced category content: {child.relative_to(root)}; classify under shared/ or project/')
    root_allowed=set(policy.get('root_files',[]))|set(CATEGORIES)
    for child in (root/'.agents').iterdir():
        if visible(child) and child.name not in root_allowed:
            fail(f'undeclared development root entry: {child.name}')
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--write-indexes',action='store_true')
    args=parser.parse_args()
    root=args.root.resolve()
    try:
        text=(root/'.agents/content-registry.yaml').read_text()
        # Give v1 a useful message before its broader YAML syntax is parsed.
        if not re.search(r'^schema_version: 2$',text,re.M):
            raise RegistryError('unsupported registry schema; use the target release upgrade command for schema 1')
        data=loads(text)
        errors=validate(root,data)
        errors+=indexes(root,data,args.write_indexes)
    except (RegistryError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        errors=[str(exc)]
    for error in errors:print('FAIL '+error,file=sys.stderr)
    if errors:return 1
    print(f'development registry: PASS ({len(data["entries"])} entries; six categories; indexes consistent)')
    return 0


if __name__=='__main__':
    sys.exit(main())
