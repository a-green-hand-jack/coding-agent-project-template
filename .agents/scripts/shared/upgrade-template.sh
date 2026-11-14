#!/usr/bin/env bash
# Apply the mechanical part of an upgrade to a newer release of the template this
# repository follows, by the rules of template-upgrade step 5:
#
#   upgrade-template.sh [--check] [--resolved PATH]... TARGET_TAG
#
# It reads the followed template and its version from the registry (step 1:
# template.upstream when present, otherwise template), fetches both tags into
# .project/state/template-upgrade/<name>.git (offline once both are there) and,
# for each path changed between them, uses the target release's registry (the
# source release's for a removed path):
#   - scope template: skipped; project-owned: left alone;
#   - `upgrade: review` (a file the project owns once it has started): never
#     changed; the release's diff is printed for review;
#   - recorded in `omitted:` (or `optional: true` and left out here): a local
#     decision, kept; a new optional path is left for a manual decision;
#   - shared: replaced above its `## In this repository` section when check 1
#     passes; without a section, replaced whole when unchanged here and
#     otherwise three-way merged with the source tag as base; added when new;
#     removed when removed and unchanged here;
#   - the registry: merged key by key and entry by entry. The `writing:` block
#     is the project's own and never changes; the followed version
#     (template.version, or template.upstream.version in a derived template) is
#     set to TARGET_TAG only when nothing conflicts.
# A local edit that the release's change overlaps, or an edit above the section,
# is a conflict: it is never overwritten, it is reported, and a three-way merge
# proposal is written under the clone's proposals/ directory. --resolved PATH
# accepts PATH (the registry too) as resolved by hand once it has no conflict
# markers left. assets/, .project/ and .env are never touched. It prints what it
# applied, skipped, refused, left for review and for manual steps, including the
# upgrade section of each release it crosses (each crossed tag's own
# RELEASE_NOTES.md; the file at a tag describes only its own release),
# and whether the light path applies. --check prints the same plan and changes
# nothing outside .project/state/template-upgrade/.
# Exit 0: done or planned without conflicts; 1: a conflict; 2: an error.
#
# A repository that does not have this script yet runs the target release's copy:
#   Extract TARGET_TAG:.agents/scripts/shared/ into .project/state/template-upgrade/
#   and run that upgrade-template.sh with its content_registry.py alongside it.
set -euo pipefail
root=$(git rev-parse --show-toplevel)
# The project's Python: AGENTS_PYTHON first, then a virtual environment at
# .project/venv, then python3 on PATH. The same order holds in the other
# inherited commands. Bytecode is never written into the source tree.
python=${AGENTS_PYTHON:-}
if [[ -z "$python" ]]; then
  python=$root/.project/venv/bin/python3
  [[ -x "$python" ]] || python=python3
fi
export PYTHONDONTWRITEBYTECODE=1
exec "$python" -I - "$(dirname "${BASH_SOURCE[0]}")" "$@" <<'PY'
import os
import posixpath
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

sys.path.insert(0, sys.argv.pop(1))
import content_registry as catalog

REGISTRY = ".agents/content-registry.yaml"
SECTION = "## In this repository"
STATE = ".project/state/template-upgrade"
NEVER = ("assets/", ".project/")
SHARED = ("shared", "shared_with_adaptation")
OWN_KEYS = ("writing",)
MARKERS = re.compile(rb"^(?:<{7}|>{7})(?: |$)", re.M)


class Failure(Exception):
    pass


def git(*args: str, cwd: Path, raw: bool = False, check: bool = True):
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True)
    if check and result.returncode:
        raise Failure(f"git {' '.join(args)}: {result.stderr.decode(errors='replace').strip()}")
    return result if not check else (result.stdout if raw else result.stdout.decode())


# --- registry -----------------------------------------------------------------

def followed_template(text: str) -> dict:
    """template-upgrade step 1: template.upstream when the block has one,
    otherwise template; with the index of the version line to move."""
    lines = text.splitlines()
    try:
        start = lines.index("template:")
    except ValueError:
        raise Failure(f"{REGISTRY} has no template: block; backfill it first (template-upgrade)")
    record: dict = {"template": {}, "upstream": {}}
    block = "template"
    for number in range(start + 1, len(lines)):
        line = lines[number]
        if line and not line[0].isspace() and not line.startswith("#"):
            break
        if line == "  upstream:":
            block = "upstream"
        match = re.match(r"^( {2}| {4})(repository|version):\s*(\S+)\s*$", line)
        if match and (match.group(1) == "  ") == (block == "template"):
            record[block][match.group(2)] = match.group(3).strip("'\"")
            if match.group(2) == "version":
                record[block]["line"] = number
    chosen = record["upstream"] or record["template"]
    if "repository" not in chosen or "version" not in chosen:
        raise Failure(f"{REGISTRY} records no template repository and version; backfill them first (template-upgrade)")
    chosen["key"] = "template.upstream.version" if record["upstream"] else "template.version"
    return chosen


def parse_registry(text: str) -> dict:
    """The registry as head (through `entries:`), entry blocks and tail. A block
    is its leading comment lines (pre) and its `- path:` item (body)."""
    lines = text.splitlines(keepends=True)
    try:
        start = next(i for i, line in enumerate(lines) if line.rstrip() == "entries:")
    except StopIteration:
        raise Failure("a registry without entries:")
    blocks: list[dict] = []
    pending: list[str] = []
    rest = start + 1
    for rest in range(start + 1, len(lines) + 1):
        if rest == len(lines):
            break
        line = lines[rest]
        match = re.match(r"^\s*- path:\s*(.+?)\s*$", line)
        if match:
            blocks.append({"path": match.group(1).strip("'\""), "pre": pending, "body": [line]})
            pending = []
        elif line.strip() and not line.lstrip().startswith("#") and line[0].isspace() and blocks and not pending:
            blocks[-1]["body"].append(line)
        elif not line.strip() or line.lstrip().startswith("#"):
            pending.append(line)
        else:
            break
    default = re.search(r"^default_scope:\s*(\S+)", text, re.M)
    return {"head": lines[:start + 1], "blocks": blocks, "tail": pending + lines[rest:],
            "default": default.group(1) if default else "project"}


def field(block: dict, name: str) -> str:
    match = re.search(rf"^\s+{name}:[ \t]*([^\n]+)", "".join(block["body"]), re.M)
    return match.group(1).strip() if match else ""


def scope_in(block: dict) -> str:
    return field(block, "scope")


def glob_pattern(pattern: str) -> re.Pattern:
    parts = re.split(r"(\*\*/|\*|\?)", pattern)
    table = {"**/": "(?:.*/)?", "*": "[^/]*", "?": "[^/]"}
    return re.compile("".join(table.get(part, re.escape(part)) for part in parts))


def entry_of(path: str, registry: dict) -> dict:
    """Most specific path wins: an exact path, then a glob, then the longest
    directory; otherwise default_scope."""
    best = (0, 0, {"path": "", "pre": [], "body": [f"  scope: {registry['default']}\n"]})
    for block in registry["blocks"]:
        pattern = block["path"]
        if pattern.endswith("/"):
            rank, matches = 1, path.startswith(pattern)
        elif any(char in pattern for char in "*?["):
            rank, matches = 2, bool(glob_pattern(pattern).fullmatch(path))
        else:
            rank, matches = 3, path == pattern
        if matches and (rank, len(pattern)) > best[:2]:
            best = (rank, len(pattern), block)
    return best[2]


def head_keys(head: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    """The top-level keys of the head (which ends with `entries:`) in order,
    each with its indented lines and the blank and comment lines before it."""
    order: list[str] = []
    blocks: dict[str, list[str]] = {}
    pending: list[str] = []
    key = None
    for line in head:
        match = re.match(r"^([A-Za-z_][\w-]*):", line)
        if match:
            key = match.group(1)
            order.append(key)
            blocks[key] = pending + [line]
            pending = []
        elif key is not None and line[:1].isspace() and line.strip():
            blocks[key] += pending + [line]
            pending = []
        else:
            pending.append(line)
    return order, blocks


OWN_LINE = re.compile(r"^(\s+(?:repository|version):)")


def without_versions(lines: list[str]) -> list[str]:
    """The template block without the values this repository records."""
    return [OWN_LINE.match(line).group(1) if OWN_LINE.match(line) else line for line in lines]


def merge_head(source: list[str], target: list[str], local: list[str], tag: str, report, conflict) -> list[str]:
    """Merge the top-level keys before `entries:`. `writing:` is the project's
    own; `template:` is compared without its repository and version values,
    which keep their local values; every other key is taken from the target
    when it is unchanged here, and is a conflict when both sides changed it."""
    (_, before), (order, after), (mine_order, mine) = head_keys(source), head_keys(target), head_keys(local)
    result = dict(mine)
    keys = list(mine_order)
    for position, key in enumerate(order):
        if key in OWN_KEYS:
            continue
        old, new, here = before.get(key), after[key], mine.get(key)
        if key == "template":
            if here is None or old is None or without_versions(old) == without_versions(new):
                continue
            if without_versions(here) == without_versions(old):
                own = {}
                for line in here:
                    if OWN_LINE.match(line):
                        own.setdefault(OWN_LINE.match(line).group(1), []).append(line)
                result[key] = [(own.get(OWN_LINE.match(line).group(1)) or [line]).pop(0)
                               if OWN_LINE.match(line) else line for line in new]
                report.applied(f"{REGISTRY}: template block as in {tag}")
            elif without_versions(here) != without_versions(new):
                report.manual(f"{REGISTRY}: the template block changed in {tag} and differs here; carry the"
                              " change over by hand, keeping this repository's own lines")
            continue
        if here is None:
            if old is None:
                anchor = next((k for k in reversed(order[:position]) if k in keys), None)
                keys.insert(keys.index(anchor) + 1 if anchor is not None else 0, key)
                result[key] = new
                report.applied(f"{REGISTRY}: {key} added")
            elif old != new:
                conflict(f"{REGISTRY}: {key} changed in {tag} and is missing here")
        elif old is None:
            if here != new:
                conflict(f"{REGISTRY}: {key} is new in {tag} and differs here")
        elif here == old and old != new:
            result[key] = new
            report.applied(f"{REGISTRY}: {key} as in {tag}")
        elif here != old and here != new and old != new:
            conflict(f"{REGISTRY}: {key} changed here and in {tag}; merge it by hand")
    for key, old in before.items():
        if key in after or key in OWN_KEYS or key not in mine or key == "entries":
            continue
        if mine[key] == old:
            keys.remove(key)
            report.applied(f"{REGISTRY}: {key} removed")
        else:
            conflict(f"{REGISTRY}: {key} removed in {tag} and changed here")
    return [line for key in keys for line in result[key]]


def merge_registry(source: dict, target: dict, local: dict, source_text: str, report, conflict) -> list[str]:
    """Apply the changes between the two releases to the local registry, the
    head key by key and the entries one by one; scope template entries are
    never taken. A conflict keeps the local text and goes to conflict()."""
    head = merge_head(source["head"], target["head"], local["head"], target["tag"], report, conflict)
    blocks = [dict(block) for block in local["blocks"]]
    index = {block["path"]: block for block in blocks}
    before = {block["path"]: block for block in source["blocks"]}
    after = {block["path"]: block for block in target["blocks"]}
    source_lines = set(source_text.splitlines(keepends=True))
    order = [block["path"] for block in target["blocks"]]
    for position, path in enumerate(order):
        new = after[path]
        old = before.get(path)
        mine = index.get(path)
        if scope_in(new) == "template":
            continue
        if old is None or (scope_in(old) == "template" and mine is None):
            if mine is None:
                pre = [line for line in new["pre"] if line.strip() and line not in source_lines]
                block = {"path": path, "pre": pre, "body": list(new["body"])}
                anchor = next((index[p] for p in reversed(order[:position]) if p in index), None)
                blocks.insert(blocks.index(anchor) + 1 if anchor else 0, block)
                index[path] = block
                report.applied(f"{REGISTRY}: entry {path} added")
            elif mine["body"] != new["body"]:
                conflict(f"{REGISTRY}: entry {path} is new in {target['tag']} and differs here")
        elif old["body"] != new["body"]:
            if mine is None:
                conflict(f"{REGISTRY}: entry {path} changed in {target['tag']} and is missing here")
            elif mine["body"] == old["body"]:
                mine["body"] = list(new["body"])
                report.applied(f"{REGISTRY}: entry {path} as in {target['tag']}")
            elif mine["body"] != new["body"]:
                conflict(f"{REGISTRY}: entry {path} changed here and in {target['tag']}")
    for path, old in before.items():
        if path in after or path not in index:
            continue
        mine = index[path]
        if mine["body"] == old["body"]:
            position = blocks.index(mine)
            blocks.pop(position)
            if position < len(blocks):
                blocks[position]["pre"] = mine["pre"] + blocks[position]["pre"]
            else:
                local["tail"] = mine["pre"] + local["tail"]
            del index[path]
            report.applied(f"{REGISTRY}: entry {path} removed")
        elif scope_in(old) != "template":
            conflict(f"{REGISTRY}: entry {path} removed in {target['tag']} and changed here")
    return head + [line for block in blocks for line in block["pre"] + block["body"]] + local["tail"]


# --- files ---------------------------------------------------------------------

def parts(text: str) -> tuple[str, str | None]:
    """template-upgrade step 5's above() and section(): the text before the
    section without trailing blank lines, and the section to the end."""
    lines = text.split("\n")
    if text.endswith("\n"):
        lines.pop()
    at = lines.index(SECTION) if SECTION in lines else len(lines)
    above = lines[:at]
    while above and above[-1] == "":
        above.pop()
    section = "".join(line + "\n" for line in lines[at:]) or None
    return "".join(line + "\n" for line in above), section


def sectioned(path: str, entry: dict) -> bool:
    """A file a project adapts in a trailing section (template-adoption step 5):
    the SKILL.md of a skill, or a memory record, registered shared_with_adaptation."""
    if scope_in(entry) != "shared_with_adaptation":
        return False
    return (entry["path"].startswith(".agents/skills/") and path == entry["path"] + "SKILL.md") or (
        entry["path"] == path and path.startswith(".agents/memory/"))


def slots(text: str) -> set[str]:
    """Slot names listed under a heading that names slots."""
    found: set[str] = set()
    listing = False
    for line in text.splitlines():
        if line.startswith("#"):
            listing = "slot" in line.lower()
        elif listing:
            match = re.match(r"\s*[-|]\s*(`[^`]+`(?:\s*,\s*`[^`]+`)*)", line)
            if match:
                found.update(re.findall(r"`([^`]+)`", match.group(1)))
    return found


def steps(text: str) -> dict[str, str]:
    """Each numbered step's text, by its number (every list with that number)."""
    found: dict[str, str] = {}
    current = None
    for line in text.splitlines():
        match = re.match(r"(\d+)\. ", line)
        if match:
            current = match.group(1)
            found[current] = found.get(current, "") + line + "\n"
        elif current and (not line.strip() or line[0].isspace()):
            found[current] += line + "\n"
        else:
            current = None
    return {number: body.rstrip() for number, body in found.items()}


def reconcile(source: tuple, target: tuple, section: str) -> list[str]:
    """Why the local section needs its slot rows or step keys reconciled."""
    reasons = []
    if slots(source[0]) != slots(target[0]):
        reasons.append("the adaptation slots changed")
    keys = {str(n) for first, last in re.findall(r"\b[Ss]teps? (\d+)(?: to (\d+))?\b", section)
            for n in range(int(first), int(last or first) + 1)}
    moved = [n for n in sorted(keys, key=int) if steps(source[0]).get(n) != steps(target[0]).get(n)]
    if moved:
        reasons.append(f"step {', '.join(moved)}, which the section is keyed to, changed")
    if source[1] != target[1] and section != source[1]:
        reasons.append("the template's own section changed")
    return reasons


class Report:
    def __init__(self) -> None:
        self.lists = {"applied": [], "skipped": [], "refused": [], "review": [], "manual": []}

    def __getattr__(self, name):
        if name in self.lists:
            return self.lists[name].append
        raise AttributeError(name)


class Upgrade:
    def __init__(self, root: Path, clone: Path, source: str, target: str, check: bool, resolved: set[str]) -> None:
        self.root, self.clone, self.source, self.target, self.check = root, clone, source, target, check
        self.resolved = resolved
        self.aliases = {}
        self.local_entries = []
        self.manual_paths = set()
        self.catalog_blocked = False
        self.proposals = clone.parent / "proposals"
        self.report = Report()
        self.path_mappings = []
        self.kept_out = set()

    def physical(self, path: str) -> str:
        matches = [(source, dest) for source, dest in self.path_mappings
                   if path == source or (source.endswith('/') and path.startswith(source))]
        if not matches:
            return path
        source, dest = max(matches, key=lambda item: (not item[0].endswith('/'), len(item[0])))
        return dest + path[len(source):]

    def blob(self, sha: str) -> bytes:
        return git("cat-file", "blob", sha, cwd=self.clone, raw=True)

    def mapped_markdown(self, path: str, data: bytes) -> bytes:
        if not self.path_mappings or not path.endswith('.md'):
            return data
        from markdown_it import MarkdownIt
        text = data.decode('utf-8')
        replacements = {}
        for token in MarkdownIt('commonmark').parse(text):
            for child in token.children or []:
                if child.type not in ('link_open', 'image'):
                    continue
                href = child.attrGet('href' if child.type == 'link_open' else 'src') or ''
                parsed = urlsplit(href)
                if parsed.scheme or parsed.netloc or parsed.path.startswith('/') or not parsed.path:
                    continue
                linked = posixpath.normpath(posixpath.join(posixpath.dirname(path), unquote(parsed.path)))
                mapped = self.physical(linked)
                if posixpath.normpath(posixpath.join(posixpath.dirname(self.physical(path)), unquote(parsed.path))) == mapped:
                    continue
                relative = posixpath.relpath(mapped, posixpath.dirname(self.physical(path)))
                replacements[href] = urlunsplit(('', '', quote(relative, safe='/._-~'), parsed.query, parsed.fragment))
        for old, new in replacements.items():
            old_syntax = '](' + old
            if text.count(old_syntax) != 1:
                raise Failure(f'mapped Markdown reference needs manual reconciliation: {path}: {old}')
            text = text.replace(old_syntax, '](' + new, 1)
        return text.encode('utf-8')

    def local(self, path: str):
        file = self.root / self.physical(path)
        if not file.exists() and not file.is_symlink() and path in self.aliases:
            file = self.root / self.physical(self.aliases[path])
        if file.is_symlink():
            return "120000", os.readlink(file).encode()
        if file.is_file():
            return ("100755" if os.access(file, os.X_OK) else "100644"), file.read_bytes()
        return ("other", b"") if file.exists() else None

    @staticmethod
    def same(state, mode: str, data: bytes) -> bool:
        return state is not None and state[1] == data and (state[0] == "120000") == (mode == "120000")

    def write(self, path: str, mode: str, data: bytes) -> None:
        if self.check:
            return
        file = self.root / self.physical(path)
        file.parent.mkdir(parents=True, exist_ok=True)
        if file.is_symlink() or file.exists():
            file.unlink()
        if mode == "120000":
            os.symlink(data.decode(), file)
        else:
            file.write_bytes(data)
            file.chmod(0o755 if mode == "100755" else 0o644)
        old = self.aliases.get(path)
        if old and self.physical(old) != self.physical(path) and ((self.root/self.physical(old)).exists() or (self.root/self.physical(old)).is_symlink()):
            self.remove(old)

    def remove(self, path: str) -> None:
        if self.check:
            return
        file = self.root / self.physical(path)
        file.unlink()
        for parent in file.parents:
            if parent == self.root or any(parent.iterdir()):
                break
            parent.rmdir()

    def merge(self, mine: str, base: str, theirs: str) -> tuple[str, bool]:
        with tempfile.TemporaryDirectory() as directory:
            names = []
            for name, text in (("mine", mine), ("base", base), ("theirs", theirs)):
                (Path(directory) / name).write_text(text, encoding="utf-8")
                names.append(str(Path(directory) / name))
            result = git("merge-file", "-p", "-L", "here", "-L", self.source, "-L", self.target, *names,
                         cwd=self.clone, check=False)
        if result.returncode < 0 or result.returncode > 127:
            raise Failure(f"git merge-file failed: {result.stderr.decode(errors='replace').strip()}")
        return result.stdout.decode(), result.returncode == 0

    def conflict(self, path: str, message: str) -> None:
        """Refuse, unless --resolved names PATH and it has no conflict markers."""
        if path not in self.resolved:
            return self.report.refused(message)
        state = self.local(path)
        if state and MARKERS.search(state[1]):
            return self.report.refused(f"{path}: --resolved, but conflict markers remain")
        self.report.applied(f"{message.split('; merge proposal')[0]}: resolved here (--resolved)")

    def propose(self, path: str, text: str, clean: bool) -> str:
        proposal = self.proposals / path
        proposal.parent.mkdir(parents=True, exist_ok=True)
        proposal.write_text(text, encoding="utf-8")
        shown = proposal.relative_to(self.root)
        return f"; merge proposal{'' if clean else ' with conflict markers'}: {shown}"

    def path(self, old_mode: str, new_mode: str, old_sha: str, new_sha: str, status: str, path: str,
             entry: dict) -> None:
        if any(catalog.rank(self.physical(path), kept) for kept in self.kept_out):
            return
        report, state, scope = self.report, self.local(path), scope_in(entry)
        local_entry = next((e for e in self.local_entries if catalog.rank(self.physical(path),e["path"])), {})
        if local_entry.get("status") in ("retired", "superseded", "rejected"):
            return report.skipped(f"{path}: local lifecycle {local_entry['status']} retained")
        if scope == "template":
            return report.skipped(f"{path}: scope template")
        if field(entry, "upgrade") == "review":
            diff = git("diff", self.source, self.target, "--", path, cwd=self.clone)
            return report.review((f"{path}: the project's own (upgrade: review); the release's change:", diff))
        if scope not in SHARED:
            return report.skipped(f"{path}: project-owned ({scope})")
        if field(entry, "optional") == "true" and state is None:
            if status == "A":
                return report.manual(f"{path}: new optional content in {self.target}; adopt it with"
                                     f" git -C {self.clone.relative_to(self.root)} show {self.target}:{path}"
                                     " or leave it out (template-adoption step 3)")
            if status == "M":
                return report.skipped(f"{path}: optional and left out here (a local decision)")
        if "160000" in (old_mode, new_mode) or (state and state[0] == "other"):
            return report.manual(f"{path}: not a file here or in the template; compare it by hand")
        if status == "A":
            data = self.mapped_markdown(path, self.blob(new_sha))
            if state is None:
                self.write(path, new_mode, data)
                return report.applied(f"{path}: added")
            if self.same(state, new_mode, data):
                return report.applied(f"{path}: already as in {self.target}")
            return self.conflict(path, f"{path}: added in {self.target}, but a different file is here")
        if status == "D":
            data = self.blob(old_sha)
            if state is None:
                return report.applied(f"{path}: already removed")
            if self.same(state, old_mode, data) or self.same(state, old_mode, self.mapped_markdown(path, data)):
                self.remove(path)
                return report.applied(f"{path}: removed")
            return self.conflict(path, f"{path}: removed in {self.target}, changed here")
        before, after = self.blob(old_sha), self.mapped_markdown(path, self.blob(new_sha))
        if state is None:
            return self.conflict(path, f"{path}: changed in {self.target}, missing here")
        if self.same(state, new_mode, after):
            if path in self.aliases and self.local(self.aliases[path]) is not None:
                self.write(path, new_mode, after)
            return report.applied(f"{path}: already as in {self.target}")
        if self.same(state, old_mode, before):
            self.write(path, new_mode, after)
            return report.applied(f"{path}: replaced")
        try:
            here, base, theirs = (data.decode("utf-8") for data in (state[1], before, after))
        except UnicodeDecodeError:
            return self.conflict(path, f"{path}: changed here (not text)")
        if path.endswith('/AGENTS.md') and all(catalog.BEGIN in text and catalog.END in text for text in (here, base, theirs)):
            expression = re.compile(re.escape(catalog.BEGIN) + r'.*?' + re.escape(catalog.END), re.S)
            placeholder = catalog.BEGIN + '\n' + catalog.END
            here, base, theirs = (expression.sub(placeholder, text) for text in (here, base, theirs))
        if "120000" in (state[0], new_mode):
            return self.conflict(path, f"{path}: changed here (a link)")
        mine, source, target = parts(here), parts(base), parts(theirs)
        if mine[1] is None:
            merged, clean = self.merge(here, base, theirs)
            if not clean:
                return self.conflict(path, f"{path}: changed here and in {self.target}"
                                           f"{self.propose(path, merged, clean)}")
            if merged == here:
                if path in self.aliases and self.local(self.aliases[path]) is not None:
                    self.write(path, new_mode, merged.encode())
                report.applied(f"{path}: already has the change of {self.target}")
            else:
                self.write(path, new_mode, merged.encode())
                report.applied(f"{path}: merged with the local text (three-way, no overlap)")
            if sectioned(path, entry):
                report.review((f"{path}: adapted here without a {SECTION} section; move the local text into"
                               f" one as additions keyed to their steps (template-upgrade step 5) and drop"
                               f" what the release covers, so that check 1 applies next time; the local"
                               f" text: git -C {self.clone.relative_to(self.root)} show {self.target}:{path}"
                               f" | diff - {path}", ""))
            return
        if mine[0] == source[0]:  # check 1
            section = target[1] if mine[1] == source[1] else mine[1]
            self.write(path, new_mode, (target[0] + ("\n" + section if section else "")).encode())
            report.applied(f"{path}: replaced above {SECTION}")
        elif mine[0] == target[0]:
            if path in self.aliases and self.local(self.aliases[path]) is not None:
                self.write(path, new_mode, here.encode())
            report.applied(f"{path}: already as in {self.target} above {SECTION}")
        else:
            merged, clean = self.merge(mine[0], source[0], target[0])
            if not (clean and merged == mine[0]):
                return self.conflict(path, f"{path}: edited above {SECTION} (check 1)"
                                           f"{self.propose(path, merged + chr(10) + mine[1], clean)}")
            if path in self.aliases and self.local(self.aliases[path]) is not None:
                self.write(path, new_mode, here.encode())
            report.applied(f"{path}: already has the change of {self.target} above {SECTION}")
        reasons = reconcile(source, target, mine[1]) if mine[1] != target[1] else []
        if reasons:
            report.manual(f"{path}: reconcile its {SECTION} section ({'; '.join(reasons)}); read"
                          f" git -C {self.clone.relative_to(self.root)} diff {self.source} {self.target} -- {path}")


# --- explicit layout/schema migration -----------------------------------------

def raw_changes(upgrade):
    raw = git("diff", "--raw", "-z", "--no-renames", "--no-abbrev", upgrade.source, upgrade.target, cwd=upgrade.clone).split("\0")
    return [(*meta[1:].split()[:4], meta[1:].split()[4][0], path)
            for meta, path in zip(raw[0::2], raw[1::2]) if meta]


def tree(upgrade, tag):
    records = git("ls-tree", "-rz", tag, cwd=upgrade.clone).split("\0")
    return {path: (meta.split()[0], meta.split()[2]) for meta, path in
            (record.split("\t", 1) for record in records if record)}


def layout_changes(upgrade):
    before, after = tree(upgrade, upgrade.source), tree(upgrade, upgrade.target)
    inverse = {old: new for new, old in upgrade.aliases.items()}
    remapped = {inverse.get(path, path): value for path, value in before.items()}
    changes = []
    for path in sorted(remapped.keys() | after.keys()):
        old, new = remapped.get(path), after.get(path)
        rewritten = bool(new and path.endswith('.md') and upgrade.path_mappings and
                         upgrade.mapped_markdown(path, upgrade.blob(new[1])) != upgrade.blob(new[1]))
        if old == new and path not in upgrade.aliases and not rewritten:
            continue
        changes.append((old[0] if old else "000000", new[0] if new else "000000",
                        old[1] if old else "0"*40, new[1] if new else "0"*40,
                        "M" if old and new else "A" if new else "D", path))
    return changes


def legacy_data(text):
    if re.search(r"^schema_version: 2$", text, re.M):
        return catalog.loads(text)
    # Schema1 is parsed with the historical block parser, preserving the raw
    # entry in provenance when folded notes are not machine-decodable.
    parsed = parse_registry(text)
    entries = []
    for block in parsed["blocks"]:
        e = {"path": block["path"], "scope": scope_in(block)}
        for key in ("id", "kind", "owner", "summary", "status", "source", "updated", "optional", "upgrade", "adoption", "supersedes", "superseded_by", "refresh_after", "retention", "retention_reason"):
            raw = field(block, key)
            if raw:
                try: e[key] = catalog.value(raw)
                except catalog.RegistryError: e[key] = "unknown"
        e["legacy_record"] = "".join(block["body"])
        entries.append(e)
    # Existing template/writing block shape is retained; no secrets are read.
    _, head = head_keys(parsed["head"])
    metadata = {}
    for key in ("template", "writing"):
        if key in head:
            metadata.update(catalog.loads("".join(head[key])))
    return {"schema_version": 1, "entries": entries, **metadata}


def complete_entry(entry, path):
    result = dict(entry)
    result["path"] = path
    result.setdefault("id", "content-" + hashlib.sha256(path.encode()).hexdigest()[:16])
    result.setdefault("kind", "skill" if path.endswith("/") and "/skills/" in path else
                      "memory" if "/memory/" in path and path.endswith(".md") else
                      "knowledge" if "/knowledge/" in path and path.endswith(".md") else "code" if path.endswith((".sh", ".py")) else "document")
    result.setdefault("owner", "unknown")
    result.setdefault("summary", "Legacy project entry; see preserved source record.")
    result.setdefault("status", "active")
    result.setdefault("source", "unknown")
    result.setdefault("updated", "unknown")
    result.setdefault("supersedes", [])
    result.setdefault("superseded_by", [])
    if result.get("scope") == "shared_with_adaptation": result.setdefault("adaptation", "Preserve local adaptation; review against source release.")
    if result["kind"] == "knowledge": result.setdefault("refresh_after", "unknown")
    return result


def legacy_reference_values(raw):
    """Only scalar/flat legacy relationship lists, never evaluated YAML tags."""
    if raw is None or raw == []:
        return []
    if isinstance(raw, list):
        if not all(isinstance(item, str) for item in raw):
            raise ValueError('relationship list must contain strings')
        return raw
    if not isinstance(raw, str):
        raise ValueError('relationship must be an ID, path, or flat list')
    text = raw.strip()
    if text in ('', 'null', '~'):
        return []
    if text.startswith('- '):
        lines = text.splitlines()
        if not all(line.strip().startswith('- ') for line in lines):
            raise ValueError('unsupported relationship list continuation')
        return [item for line in lines for item in legacy_reference_values(line.strip()[2:])]
    if text.startswith('['):
        try:
            return legacy_reference_values(json.loads(text))
        except json.JSONDecodeError:
            if not text.endswith(']'):
                raise ValueError('unfinished relationship list')
            return [item for part in text[1:-1].split(',') for item in legacy_reference_values(part)]
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ('"', "'"):
        return [text[1:-1]]
    return [text]


def reconcile_lifecycle(upgrade, entries, original, target, upstream_ids, pending_writes):
    by_id = {entry['id']: entry for entry in entries}
    by_path = {entry['path']: entry for entry in entries}
    inverse = {old: new for new, old in upgrade.aliases.items()}
    pattern = re.compile(r'^(scope|status|supersedes|superseded_by|refresh_after):[^\n]*(?:\n[ \t]+[^\n]*)*\n?', re.M)

    def held(path, detail):
        upgrade.report.refused(f'{path}: unresolved lifecycle reference ({detail}); source history held')
        upgrade.catalog_blocked = True

    def resolve_refs(entry, raw, key):
        resolved = []
        try:
            values = legacy_reference_values(raw)
        except ValueError as exc:
            held(entry['path'], str(exc))
            return []
        for ref in values:
            candidates = {ref} if ref in by_id else set()
            if ref in upstream_ids:
                candidates.add(upstream_ids[ref])
            if not candidates:
                owner_paths = (entry['path'], upgrade.aliases.get(entry['path'], entry['path']))
                paths = {ref} | {os.path.normpath(str(Path(owner).parent / ref)) for owner in owner_paths}
                paths |= {inverse.get(path, path) for path in list(paths)}
                candidates = {by_path[path]['id'] for path in paths if path in by_path}
            if not candidates and '/' not in ref:
                candidates = {e['id'] for e in entries if Path(e['path'].rstrip('/')).name == ref}
            if len(candidates) != 1:
                # Known upstream prose descriptions were already explicitly
                # retained as historical metadata; they are not active edges.
                historical = next((e.get('legacy_lifecycle', {}) for e in target['entries']
                                   if e['path'] == entry['path']), {})
                if not historical:
                    # Follow explicit upstream history even when the template-only
                    # destination is not adopted and local ownership stays put.
                    destination_ids = {dest['id'] for migration in target.get('migrations', [])
                                       if any(src['path'] == entry['path'] for src in migration['from'])
                                       for dest in migration.get('to', [])}
                    historical = next((e.get('legacy_lifecycle', {}) for e in target['entries']
                                       if e['id'] in destination_ids and e['scope'] == 'template'), {})
                if not candidates and historical.get(key) == ref and entry['status'] == 'active':
                    entry.setdefault('legacy_lifecycle', {})[key] = ref
                    continue
                held(entry['path'], f'{key}: {ref!r}, {len(candidates)} matching identities')
                continue
            resolved.append(next(iter(candidates)))
        return list(dict.fromkeys(resolved))

    for entry in entries:
        path = entry['path']
        values = {key: entry.get(key, []) for key in ('supersedes', 'superseded_by')}
        state = (pending_writes.get(path) or upgrade.local(path)) if entry['kind'] in ('memory', 'knowledge') else None
        if state and state[0] != '120000' and entry['scope'] == 'project':
            body = state[1].decode()
            split = body.split('---', 2) if body.startswith('---\n') else []
            removed = {}
            front = split[1] if len(split) == 3 else ''
            for match in pattern.finditer(front):
                removed[match.group(1)] = match.group(0).split(':', 1)[1].strip()
            explicit = original.get(upgrade.aliases.get(path, path), original.get(path, {}))
            if 'status' in removed:
                statuses = legacy_reference_values(removed['status'])
                status = statuses[0] if len(statuses) == 1 else 'unknown'
                if explicit.get('status') and explicit['status'] != status:
                    held(path, 'registry and frontmatter disagree on status')
                entry['status'] = status
            if 'refresh_after' in removed:
                entry['refresh_after'] = removed['refresh_after']
            for key in ('supersedes', 'superseded_by'):
                if key in removed:
                    if legacy_reference_values(values[key]):
                        old = resolve_refs(entry, values[key], key)
                        new = resolve_refs(entry, removed[key], key)
                        if set(old) != set(new):
                            held(path, f'registry and frontmatter disagree on {key}')
                    values[key] = removed[key]
            if removed:
                entry.setdefault('legacy_frontmatter', {}).update(removed)
                pending_writes[path] = (state[0], ('---' + pattern.sub('', front) + '---' + split[2]).encode())
        for key, value in values.items():
            entry[key] = resolve_refs(entry, value, key)
        if state and entry['status'] in ('superseded', 'retired'):
            entry.setdefault('retention', 'historical')
            entry.setdefault('retention_reason', 'Preserve the existing decision body and source evidence; not current guidance.')
        if entry['status'] not in catalog.STATUSES:
            held(path, 'invalid lifecycle status')
        if entry.get('retention') and not catalog.historical_body(entry):
            held(path, 'invalid historical retention policy')


def prepare_layout(upgrade, source_text, target_text, local_text):
    target = catalog.loads(target_text)
    local = legacy_data(local_text)
    source = legacy_data(source_text)
    report = upgrade.report
    result = json.loads(json.dumps(target))
    local_roots = local.get('policy', {}).get('root_files', [])
    target_roots = result.setdefault('policy', {}).setdefault('root_files', [])
    for name in local_roots:
        if name not in target_roots:
            target_roots.append(name)
    if upgrade.path_mappings:
        result['path_mappings'] = local['path_mappings']
    pending_writes = {}
    upstream_ids = {}
    def omitted_already(record):
        return any(x.get('id') == record.get('id') or x.get('path') == record.get('path') for x in result['omitted'])
    result['omitted'] = []
    for omitted in [*local.get('omitted', []), *target.get('omitted', [])]:
        if not omitted_already(omitted):
            result['omitted'].append(omitted)
    for e in target['entries']:
        if e['scope']=='template' and not omitted_already(e):
            result['omitted'].append({'id':e['id'],'path':e['path'],'reason':'Upstream template-only content; not adopted.'})
    result["template"] = local["template"]
    if "writing" in local: result["writing"] = local["writing"]
    else: result.pop("writing", None)
    # Historical metadata remains history, never an active competing catalog.
    if local["schema_version"] == 1:
        result["local_legacy_inventory"] = {"version": upgrade.source, "entries": local["entries"]}
    elif "local_legacy_inventory" in local:
        result["local_legacy_inventory"] = local["local_legacy_inventory"]
    for migration in target.get("migrations", []):
        if migration.get("entity") == "registration":continue
        old, new = migration["from"], migration.get("to", [])
        # Template-only entries are not adopted. A legacy project can own a
        # file at the old upstream path; never relocate it as template content.
        target_by_id = {entry["id"]: entry for entry in target["entries"]}
        if new and all(target_by_id.get(item["id"], {}).get("scope") == "template" for item in new):
            continue
        if len(old) != 1 or len(new) != 1:
            affected={x['path'] for x in old+new}
            upgrade.manual_paths.update(affected)
            if any(upgrade.local(x["path"]) for x in old):
                report.manual(f"migration {migration['action']}: {old} -> {new}; reconcile many-to-many content by hand")
                if not affected.issubset(upgrade.resolved):
                    report.refused("many-to-many migration requires reviewed --resolved for every source and destination; all affected files held")
            continue
        if old[0]["path"] != new[0]["path"]:
            old_path,new_path=old[0]['path'],new[0]['path']
            old_state = upgrade.local(old_path)
            destination = upgrade.root / upgrade.physical(new_path)
            new_state = upgrade.local(new_path) if destination.exists() or destination.is_symlink() else None
            if old_state and new_state and old_state != new_state:
                upgrade.manual_paths.update((old_path, new_path))
                report.refused(f'{old_path} -> {new_path}: conflicting existing destination; both files held')
            previous = upgrade.aliases.get(new_path)
            previous_state = upgrade.local(previous) if previous else None
            if previous and previous != old_path and previous_state and old_state:
                upgrade.manual_paths.update((previous, old_path, new_path))
                report.refused(f'{previous} and {old_path} both map to {new_path}; preserve both and resolve manually')
            if not previous or old_state or not previous_state:
                upgrade.aliases[new_path] = old_path
    local_by_id = {entry.get('upstream_id', entry.get('id')): entry for entry in local['entries']
                   if entry.get('upstream_id', entry.get('id'))}
    inverse_aliases = {old: new for new, old in upgrade.aliases.items()}
    for target_entry in target['entries']:
        if target_entry.get('scope') != 'project':
            continue
        new_path = target_entry['path']
        old_path = upgrade.aliases.get(new_path)
        mine = local_by_id.get(target_entry['id']) or next(
            (entry for entry in local['entries'] if entry.get('scope') == 'project' and entry['path'] == old_path), None)
        if old_path and not mine and local.get('schema_version') == 1:
            legacy_owner = entry_of(old_path, parse_registry(local_text))
            if scope_in(legacy_owner) == 'project':
                mine = {'path': old_path}
        if not old_path or not mine or mine['path'] != old_path:
            continue
        source_file = upgrade.root / upgrade.physical(old_path)
        if any(parent.is_symlink() for parent in source_file.parents if parent != upgrade.root and upgrade.root in parent.parents):
            report.refused(f'{old_path}: project-owned source has a symbolic-link parent')
            upgrade.catalog_blocked = True
            continue
        old_state = upgrade.local(old_path)
        if old_state is None:
            continue
        destination = upgrade.root / upgrade.physical(new_path)
        if any(parent.is_symlink() for parent in destination.parents if parent != upgrade.root and upgrade.root in parent.parents):
            report.refused(f'{old_path} -> {new_path}: project-owned destination has a symbolic-link parent')
            upgrade.catalog_blocked = True
            continue
        if destination.exists() or destination.is_symlink():
            report.refused(f'{old_path} -> {new_path}: project-owned destination already exists; preserve both and resolve manually')
            upgrade.catalog_blocked = True
            continue
        if old_state[0] not in ('100644', '100755'):
            report.refused(f'{old_path}: project-owned record is not a regular file; preserve and resolve manually')
            upgrade.catalog_blocked = True
            continue
        try:
            text = old_state[1].decode('utf-8')
            from markdown_it import MarkdownIt
            replacements = {}
            for token in MarkdownIt('commonmark').parse(text):
                for child in token.children or []:
                    if child.type not in ('link_open', 'image'):
                        continue
                    href = child.attrGet('href' if child.type == 'link_open' else 'src') or ''
                    parsed = urlsplit(href)
                    if parsed.scheme or parsed.netloc or parsed.path.startswith('/') or not parsed.path:
                        continue
                    linked = posixpath.normpath(posixpath.join(posixpath.dirname(old_path), unquote(parsed.path)))
                    destination_path = inverse_aliases.get(linked, linked)
                    relative = posixpath.relpath(destination_path, posixpath.dirname(new_path))
                    updated = urlunsplit(('', '', quote(relative, safe='/._-~'), parsed.query, parsed.fragment))
                    if updated != href:
                        replacements[href] = updated
            for old_href, new_href in replacements.items():
                syntax = '](' + old_href
                if text.count(syntax) != 1:
                    raise ValueError(f'ambiguous Markdown link {old_href}')
                text = text.replace(syntax, '](' + new_href, 1)
            pending_writes[new_path] = (old_state[0], text.encode('utf-8'))
            report.applied(f'{old_path} -> {new_path}: preserve project-owned record')
        except (UnicodeDecodeError, ValueError, ImportError) as exc:
            report.refused(f'{old_path}: cannot safely relocate project-owned record: {exc}')
            upgrade.catalog_blocked = True

    # Local hook names had a defined caller in schema1; move without rewriting
    # their contents. Other flat local items follow their existing scope.
    known = {x["path"] for x in target["entries"]}
    source_files = tree(upgrade, upgrade.source)
    local_files = catalog.git_files(upgrade.root)
    local_moves = {}
    for path in local_files:
        parts = Path(path).parts
        if len(parts) < 3 or parts[0] != ".agents" or parts[1] not in catalog.CATEGORIES:
            continue
        if parts[2] in ("shared", "project", "AGENTS.md", "CLAUDE.md", "entry-template.md", "ENTRY_TEMPLATE.md") or path in source_files:
            continue
        legacy = entry_of(path, parse_registry(local_text))
        explicit = legacy['path']==path or len(Path(legacy['path']).parts)>=3
        group = "shared" if explicit and scope_in(legacy) in SHARED else "project"
        if parts[-1] in ('setup-project.sh','migrate-project.rules'): group='project'
        new = "/".join((*parts[:2], group, *parts[2:]))
        local_moves[path] = new
        upgrade.aliases[new] = path
        if (upgrade.root/new).exists() and upgrade.local(new) != upgrade.local(path):
            upgrade.conflict(new, f"{path} -> {new}: destination contains different local content")
            continue
        report.applied(f"{path} -> {new}: preserve local content")
        state = upgrade.local(path)
        if state: pending_writes[new] = state
    inverse = {old: new for new, old in upgrade.aliases.items()}
    def mapped(path):
        if path in inverse:return inverse[path]
        if path.endswith('/'):
            destinations={"/".join(new.split("/")[:-len(old[len(path):].split("/"))])+"/"
                          for old,new in inverse.items() if old.startswith(path) and old[len(path):]}
            if len(destinations)==1:return destinations.pop()
        return path
    original = {e["path"]: e for e in local["entries"]}
    before = {e["path"]: e for e in source["entries"]}
    used = set()
    entries = []
    for e in target["entries"]:
        if e["scope"] == "template":
            continue
        path = e["path"]
        old_path = upgrade.aliases.get(path, path)
        mine = original.get(upgrade.physical(old_path)) or original.get(upgrade.physical(path))
        if mine: used.add(mine["path"])
        new = dict(e)
        if mine:
            # Keep explicit local decisions and source identities. Unchanged
            # source metadata advances; changed ownership/lifecycle never resets.
            baseline = before.get(old_path, {})
            for key, val in mine.items():
                if key in ("path", "legacy_record"): continue
                if key == "id" or (key in baseline and baseline[key] != val) or key not in baseline:
                    new[key] = val
            if local["schema_version"] == 1:
                new.pop("legacy_record", None)
        entry = complete_entry(new, upgrade.physical(path))
        entries.append(entry)
        if e["id"] != entry["id"]:
            upstream_ids[e["id"]] = entry["id"]
    target_paths = {e["path"] for e in entries}
    source_by_id = {e.get('id'): e for e in source['entries']}
    target_ids = {e.get('id') for e in target['entries']}
    removed_local = []
    for e in local["entries"]:
        if e["path"] in used: continue
        identity = e.get('upstream_id', e.get('id'))
        # A mapped upstream deletion is handled by the file conflict check;
        # do not leave an active registration for an unchanged deleted file.
        if (upgrade.path_mappings and identity in source_by_id and identity not in target_ids
                and source_by_id[identity].get('scope') in SHARED
                and upgrade.physical(source_by_id[identity]['path']) == e['path']):
            removed_local.append(e['path'])
            continue
        path = mapped(e["path"])
        if e["scope"] == "template":
            if "upstream" not in local.get("template", {}):
                continue
            if path in target_paths:
                report.refused(f'{path}: local template-only identity collides with upstream content')
                upgrade.catalog_blocked = True
            else:
                entries.append(complete_entry(e, path)); target_paths.add(path)
            continue
        # Schema1 inherited defaults are historical classification, not units.
        # Exact local entries, including retired paths, stay registered.
        if local["schema_version"] == 1 and (any(x in path for x in '*?[') or path.endswith('/') and e.get("kind") not in ("skill", "code")):
            continue
        if path in target_paths: continue
        if e["scope"] == "project" and path.endswith('/') and not any(p.startswith(e['path']) for p in local_files): continue
        entries.append(complete_entry(e, path));target_paths.add(path)
    for old, new in local_moves.items():
        if any(catalog.rank(new,e['path']) for e in entries): continue
        if '/skills/' in new:
            old='/'.join(old.split('/')[:3])+'/'
            new='/'.join(new.split('/')[:4])+'/'
        e={"path":old,"scope":"project","source":{"version":upgrade.source,"path":old}}
        entries.append(complete_entry(e,new))
    # Register preserved local documents individually, including historical
    # upstream project content that was never reusable template payload.
    for path in local_files:
        new_path = inverse.get(path,path)
        if any(catalog.rank(path, removed) for removed in removed_local):
            continue
        if not new_path.startswith(".agents/") or new_path == REGISTRY:
            continue
        if any(catalog.rank(new_path,e["path"]) for e in entries):
            continue
        if path in source_files and not ("/project/" in path):
            continue
        legacy = entry_of(path,parse_registry(local_text))
        if scope_in(legacy) == "template":continue
        e = complete_entry({"path":path,"scope":"project","source":{"version":upgrade.source,"path":path}},new_path)
        # Schema1 project-owned content has no stable ID. Its path-derived ID
        # can collide with a now-template-only upstream identity after a rename.
        if local["schema_version"] == 1 and any(t["id"] == e["id"] and t["scope"] == "template" for t in target["entries"]):
            e["id"] = "local-" + e["id"]
        entries.append(e)
        report.skipped(f"{new_path}: project-owned (preserved legacy content)")
    if local['schema_version'] == 2:
        legacy = local.get('local_legacy_inventory', {}).get('entries', [])
        by_id = {}
        for entry in entries:
            by_id.setdefault(entry['id'], []).append(entry)
        for identity, group in by_id.items():
            projects = [e for e in group if e.get('scope') == 'project']
            shared = [e for e in group if e.get('scope') in SHARED]
            omitted_template = [e for e in target['entries'] if e.get('id') == identity and e.get('scope') == 'template']
            if len(projects) != 1 or not ((len(group) == 2 and len(shared) == 1) or
                                          (len(group) == 1 and len(omitted_template) == 1 and
                                           omitted_template[0]['path'] != projects[0]['path'])):
                continue
            project = projects[0]
            matches = [e for e in legacy if e.get('scope') == 'project' and not e.get('id')
                       and identity == 'content-' + hashlib.sha256(e['path'].encode()).hexdigest()[:16]
                       and (e['path'] == project['path'] or
                            '/'.join((*Path(e['path']).parts[:2], 'project', *Path(e['path']).parts[2:])) == project['path'])]
            source = project.get('source')
            if not matches and isinstance(source, dict) and source.get('path') == project['path'] and source.get('version') == local.get('local_legacy_inventory', {}).get('version'):
                if identity == 'content-' + hashlib.sha256(project['path'].encode()).hexdigest()[:16]:
                    owners = [e for e in legacy if catalog.rank(project['path'], e['path'])]
                    owner = max(owners, key=lambda e: catalog.rank(project['path'], e['path'])) if owners else {}
                    if owner.get('scope') == 'project' and not owner.get('id'):
                        matches.append(source)
            referenced = any(identity in e.get(key, []) for e in local['entries']
                             for key in ('supersedes', 'superseded_by'))
            replacement = 'local-' + identity
            if len(matches) == 1 and not referenced and replacement not in by_id:
                project['id'] = replacement
                project['legacy_generated_id'] = identity
                for migration in result.get('migrations', []):
                    for destination in migration.get('to', []):
                        if destination.get('id') == identity and destination.get('path') == project['path']:
                            destination['id'] = replacement
            elif len(group) == 1:
                report.refused(f"{identity}: project identity collides with omitted upstream content; provenance or references need review")
                upgrade.catalog_blocked = True
    # Resolve the whole graph before removing any frontmatter or moving local
    # files. A failed preflight preserves source bytes and the source registry.
    reconcile_lifecycle(upgrade, entries, original, target, upstream_ids, pending_writes)
    result["entries"] = entries
    local_template_entries = {entry['id']: entry for entry in entries if entry['scope'] == 'template'}
    result['omitted'] = [entry for entry in result['omitted'] if entry.get('id') not in local_template_entries]
    recorded = local.get('omitted', [])
    template_only = {entry['id'] for entry in target['entries'] if entry['scope'] == 'template'}
    local_ids = {entry.get('id') for entry in local['entries']}
    for entry in list(entries):
        path = entry['path']
        omissions = [x for x in result['omitted'] if x.get('id') == entry['id']
                     or (x.get('path') == path and x.get('id') not in template_only)]
        present = upgrade.local(path) is not None
        status = entry.get('status', 'active')
        if not omissions:
            if (status == 'active' and entry.get('optional') and not present and entry['id'] in local_ids
                    and entry['scope'] != 'template' and not omitted_already(entry)):
                entries.remove(entry)
                upgrade.kept_out.add(upgrade.physical(path))
                result['omitted'].append({'id': entry['id'], 'path': path,
                                          'reason': 'Optional content left out here (recorded from an optional entry without a file).'})
                report.applied(f"omitted: {path} (optional entry without a file recorded as an omission)")
            continue
        local_records = [x for x in omissions if x in recorded]
        if status != 'active':
            if present:
                report.refused(f"{path}: local status {status} and omitted, but the file is present; reconcile by hand")
                upgrade.catalog_blocked = True
                continue
            result['omitted'] = [x for x in result['omitted'] if x not in omissions]
            upgrade.kept_out.add(upgrade.physical(path))
            if local_records:
                reasons = '; '.join(x.get('reason', '') for x in local_records)
                report.skipped(f"kept {status}: {path} (redundant omission dropped: {reasons})")
        elif present:
            result['omitted'] = [x for x in result['omitted'] if x not in omissions]
            if local_records and any(x.get('id') in template_only for x in local_records):
                report.applied(f"project-owned: {path} (template-only omission dropped; file present)")
            elif local_records:
                report.applied(f"adopted: {path} (omission dropped; file present)")
        else:
            entries.remove(entry)
            upgrade.kept_out.add(upgrade.physical(path))
            for upstream, current in list(upstream_ids.items()):
                if current == entry['id']:
                    del upstream_ids[upstream]
            report.skipped(f"kept out: {path} (omitted {'locally' if local_records else 'in ' + upgrade.target})")
    if local["schema_version"] == 2:
        # Preserve local policy exceptions and history in addition to upstream.
        exceptions = result["policy"]["naming_exceptions"]
        for item in local.get("policy",{}).get("naming_exceptions",[]):
            if item not in exceptions: exceptions.append(item)
        for item in local.get("migrations",[]):
            if item not in result["migrations"]:result["migrations"].append(item)
    for migration in result.get('migrations', []):
        for destination in migration.get('to', []):
            destination['path'] = upgrade.physical(destination['path'])
            old_id = destination['id']
            if old_id in upstream_ids:
                destination.setdefault('upstream_id', old_id)
                destination['id'] = upstream_ids[old_id]
            current_entry = next((entry for entry in entries if entry['id'] == destination['id']), None)
            if current_entry and not catalog.rank(destination['path'], current_entry['path']):
                destination.setdefault('upstream_path', destination['path'])
                destination['path'] = current_entry['path']
            local_template = local_template_entries.get(destination['id'])
            upstream_template = next((entry for entry in target['entries']
                                      if entry['id'] == old_id and entry['scope'] == 'template'), None)
            if local_template and upstream_template and not catalog.rank(destination['path'], local_template['path']):
                destination.setdefault('upstream_path', destination['path'])
                destination['path'] = local_template['path']
    unique_migrations = []
    for migration in result.get('migrations', []):
        if migration not in unique_migrations:
            unique_migrations.append(migration)
    result['migrations'] = unique_migrations
    for message in catalog.relationship_errors(entries):
        report.refused(message)
        upgrade.catalog_blocked = True
    if upgrade.catalog_blocked:
        report.lists['applied'].clear()
        report.manual('identity/lifecycle preflight failed; no project source files or registry changed')
    else:
        for path, (mode, data) in pending_writes.items():
            upgrade.write(path, mode, data)
    if not upgrade.catalog_blocked:
        report.applied(f"{REGISTRY}: explicit schema {local['schema_version']} -> 2 and identity/path migration")
    return result


# --- release notes -------------------------------------------------------------

def crossed_releases(source: str, target: str, notes_at) -> tuple[list[tuple[str, str | None]], list[str]]:
    """Each release after source up to target, newest first, with the manual
    steps of its upgrade section (None when it is marked **Command only.**).
    Each crossed release is read from its own RELEASE_NOTES.md, because the file
    describes only the current release; every entry names its predecessor in
    `### Upgrading a project from <previous tag>`. notes_at(tag) returns that
    tag's notes, or None when they cannot be read."""
    crossed: list[tuple[str, str | None]] = []
    problems: list[str] = []
    tag, seen = target, set()
    while tag != source:
        if tag in seen:
            problems.append(f"the release notes point back to {tag}; read the releases after it by hand")
            break
        seen.add(tag)
        notes = notes_at(tag)
        if notes is None:
            problems.append(f"cannot read RELEASE_NOTES.md at {tag}; read that release and the older crossed"
                            " ones by hand")
            break
        entries = {entry.split(None, 1)[0] if entry.strip() else "": entry
                   for entry in re.split(r"^## ", notes, flags=re.M)[1:]}
        entry = entries.get(tag)
        if entry is None:
            problems.append(f"RELEASE_NOTES.md at {tag} has no `## {tag}` entry; read that release by hand")
            break
        match = re.search(r"^### Upgrading\b.*?\n(.*?)(?=^### |\Z)", entry, re.M | re.S)
        if not match:
            crossed.append((tag, "(no upgrade section: read the whole entry)"))
        elif match.group(1).strip().startswith("**Command only.**"):
            crossed.append((tag, None))
        else:
            crossed.append((tag, match.group(1).strip()))
        previous = re.search(r"^### Upgrading\b[^\n]*?\bfrom\s+(\S+)", entry, re.M)
        if previous is None:
            problems.append(f"RELEASE_NOTES.md at {tag} names no `### Upgrading a project from <tag>`"
                            " predecessor; read the older crossed releases by hand")
            break
        tag = previous.group(1).strip("'\".,;:")
    return crossed, problems


# --- main ----------------------------------------------------------------------

def fetch(clone: Path, repository: str, tags: tuple[str, ...]) -> None:
    if not (clone / "HEAD").exists():
        clone.parent.mkdir(parents=True, exist_ok=True)
        git("init", "-q", "--bare", str(clone), cwd=clone.parent)
    for tag in tags:
        if git("rev-parse", "-q", "--verify", f"refs/tags/{tag}^{{commit}}", cwd=clone, check=False).returncode:
            git("fetch", "-q", "--no-tags", "--depth=1", repository, f"+refs/tags/{tag}:refs/tags/{tag}", cwd=clone)


def main(arguments: list[str]) -> int:
    check, resolved, rest = False, set(), []
    arguments = list(arguments)
    while arguments:
        argument = arguments.pop(0)
        if argument == "--check":
            check = True
        elif argument == "--resolved" and arguments and not arguments[0].startswith("-"):
            resolved.add(os.path.normpath(arguments.pop(0)))
        else:
            rest.append(argument)
    if len(rest) != 1 or rest[0].startswith("-"):
        print("usage: upgrade-template.sh [--check] [--resolved PATH]... TARGET_TAG", file=sys.stderr)
        return 2
    target = rest[0]
    root = Path(git("rev-parse", "--show-toplevel", cwd=Path.cwd()).strip())
    registry_text = (root / REGISTRY).read_text(encoding="utf-8")
    followed = followed_template(registry_text)
    source, repository = followed["version"], followed["repository"]
    if source == target:
        print(f"{followed['key']} is already {target}")
        return 0
    name = re.sub(r"\.git$", "", repository.rstrip("/").rsplit("/", 1)[-1])
    clone = root / STATE / f"{name}.git"
    fetch(clone, repository, (source, target))
    upgrade = Upgrade(root, clone, source, target, check, resolved)
    shutil.rmtree(upgrade.proposals, ignore_errors=True)
    report = upgrade.report

    shown = lambda tag: git("show", f"{tag}:{REGISTRY}", cwd=clone)
    source_registry, target_registry = shown(source), shown(target)
    registries = {"before": parse_registry(source_registry), "after": parse_registry(target_registry)}
    registries["after"]["tag"] = target
    schema2 = re.search(r"^schema_version: 2$", target_registry, re.M) is not None
    local_v2 = None
    if schema2:
        try:
            from markdown_it import MarkdownIt
        except ImportError:
            raise Failure('schema 2 upgrades require markdown-it-py; install it before retrying')
        # Schema migrations describe upstream moves, not arbitrary adopter path
        # mappings. Do not silently recreate an upstream path or overwrite a
        # locally relocated identity when its mapping semantics are unknown.
        local_data = legacy_data(registry_text)
        source_data = legacy_data(source_registry)
        target_data = catalog.loads(target_registry)
        mappings = local_data.get('path_mappings', [])
        if not isinstance(mappings, list):
            raise Failure('path_mappings must be a list of from/to records')
        seen_sources, seen_destinations = set(), set()
        for mapping in mappings:
            if not isinstance(mapping, dict) or set(mapping) != {'from', 'to'}:
                raise Failure('each path mapping must contain only from and to')
            source_path, destination = mapping['from'], mapping['to']
            if not catalog.safe_path(source_path) or not catalog.safe_path(destination) or not source_path.startswith('.agents/') or not destination.startswith('.agents/') or source_path.endswith('/') != destination.endswith('/'):
                raise Failure('unsafe path mapping; use matching file or directory paths within .agents/')
            if source_path == REGISTRY or destination == REGISTRY:
                raise Failure('the registry cannot be relocated')
            if source_path in seen_sources or destination in seen_destinations or source_path == destination:
                raise Failure('ambiguous or duplicate path mapping')
            if source_path.startswith(destination) or destination.startswith(source_path):
                raise Failure('overlapping source and destination mapping')
            for parent in (root/destination.rstrip('/')).parents:
                if parent == root: break
                if parent.is_symlink(): raise Failure('mapping destination contains a symbolic-link parent')
            seen_sources.add(source_path); seen_destinations.add(destination)
            upgrade.path_mappings.append((source_path, destination))
        for i, (source_path, destination) in enumerate(upgrade.path_mappings):
            for other_source, other_destination in upgrade.path_mappings[i + 1:]:
                if destination.startswith(other_destination) or other_destination.startswith(destination):
                    raise Failure('overlapping mapping destinations are ambiguous')
                if source_path.startswith(other_destination) or other_source.startswith(destination):
                    raise Failure('mapping destination overlaps another source')
        if mappings:
            upstream_files = set(tree(upgrade, source)) | set(tree(upgrade, target))
            for source_path, _ in upgrade.path_mappings:
                if not any(p == source_path or source_path.endswith('/') and p.startswith(source_path) for p in upstream_files):
                    raise Failure(f'mapping source not present in either release: {source_path}')
            local_ids = {e.get('upstream_id', e.get('id')): e for e in local_data.get('entries', [])}
            upstream_entries = target_data.get('entries', []) + source_data.get('entries', [])
            mapped_destinations = {}
            for upstream_path in upstream_files:
                local_path = upgrade.physical(upstream_path)
                if local_path == upstream_path:
                    continue
                if local_path in mapped_destinations and mapped_destinations[local_path] != upstream_path:
                    raise Failure(f'mapping collision at {local_path}')
                if local_path in upstream_files and upgrade.physical(local_path) == local_path:
                    raise Failure(f'mapping collides with an unmapped upstream path: {local_path}')
                mapped_destinations[local_path] = upstream_path
                original_path, mapped_path = root/upstream_path, root/local_path
                if original_path.exists() or original_path.is_symlink():
                    raise Failure(f'both mapped and original locations require review: {upstream_path}')
                if mapped_path.exists() or mapped_path.is_symlink():
                    owners = [e for e in upstream_entries if catalog.rank(upstream_path, e.get('path', ''))]
                    if not any(e.get('id') in local_ids and catalog.rank(local_path, local_ids[e['id']]['path']) for e in owners):
                        raise Failure(f'mapped destination is not owned by the upstream identity: {local_path}')
            try:
                from markdown_it import MarkdownIt
            except ImportError:
                raise Failure('mapped upgrades require markdown-it-py for reference preflight')
        if mappings and not check:
            # Preflight every mapped operation before touching the checkout.
            status = main(['--check', *sum((['--resolved', p] for p in sorted(resolved)), []), target])
            if status:
                raise Failure('mapped upgrade preflight failed; no source files or registry were changed')
        if local_data.get('schema_version') == 2 and source_data.get('schema_version') == 2:
            before = {e['id']: e for e in source_data['entries']}
            after = {e['id']: e for e in target_data['entries']}
            for entry in local_data['entries']:
                identity = entry.get('upstream_id', entry.get('id'))
                if identity not in before or identity not in after:
                    continue
                local_path = entry['path']
                expected = (upgrade.physical(before[identity]['path']), upgrade.physical(after[identity]['path']))
                if local_path not in expected:
                    raise Failure(f'{identity}: locally relocated path {local_path}; automatic mapping is unsupported; reconcile the upgrade manually before advancing the version')
        if not check and not mappings:
            project_ids = {entry['id'] for entry in target_data.get('entries', []) if entry.get('scope') == 'project'}
            project_moves = any(
                len(migration.get('from', [])) == len(migration.get('to', [])) == 1
                and migration['to'][0]['id'] in project_ids
                and migration['from'][0]['path'] != migration['to'][0]['path']
                and (root / migration['from'][0]['path']).is_file()
                for migration in target_data.get('migrations', [])
            )
            if project_moves:
                status = main(['--check', *sum((['--resolved', p] for p in sorted(resolved)), []), target])
                if status:
                    raise Failure('project record migration preflight failed; no source files or registry were changed')
        local_v2 = prepare_layout(upgrade, source_registry, target_registry, registry_text)
        upgrade.local_entries = local_v2["entries"]
    changes = [] if upgrade.catalog_blocked else layout_changes(upgrade) if schema2 else raw_changes(upgrade)
    for old_mode, new_mode, old_sha, new_sha, status, path in changes:
        if path == REGISTRY or path in upgrade.manual_paths:
            continue
        if path.startswith(NEVER) or path == ".env":
            report.manual(f"{path}: changed in {target}; this command never touches it, compare it by hand")
            continue
        old_path = upgrade.aliases.get(path, path)
        entry = entry_of(old_path if status == "D" else path, registries["before" if status == "D" else "after"])
        upgrade.path(old_mode, new_mode, old_sha, new_sha, status, path, entry)

    if schema2:
        merged_text = catalog.dumps(local_v2)
        if not report.lists["refused"]:
            chosen = local_v2["template"].get("upstream", local_v2["template"])
            chosen["version"] = target
            merged_text = catalog.dumps(local_v2)
        if not check and not upgrade.catalog_blocked:
            (root / REGISTRY).write_text(merged_text, encoding="utf-8")
            catalog.indexes(root, local_v2, write=True)
            for old_path in upgrade.aliases.values():
                parent=(root/old_path).parent
                while parent != root and len(parent.relative_to(root).parts)>2 and parent.exists() and not any(parent.iterdir()):
                    parent.rmdir()
                    parent=parent.parent
    else:
        merged = merge_registry(registries["before"], registries["after"], parse_registry(registry_text),
                                source_registry, report, lambda message: upgrade.conflict(REGISTRY, message))
        if not report.lists["refused"]:
            number = followed_template("".join(merged))["line"]
            merged[number] = re.sub(r"(version:\s*)\S+", lambda m: m.group(1) + target, merged[number], count=1)
        if "".join(merged) != registry_text and not check:
            (root / REGISTRY).write_text("".join(merged), encoding="utf-8")

    def notes_at(tag: str):
        """A tag's own release notes; a crossed tag is fetched when the cache
        has only the two ends. None when the tag or its file cannot be read."""
        if git("rev-parse", "-q", "--verify", f"refs/tags/{tag}^{{commit}}", cwd=clone,
               check=False).returncode:
            try:
                fetch(clone, repository, (tag,))
            except Failure:
                return None
        shown = git("show", f"{tag}:RELEASE_NOTES.md", cwd=clone, check=False)
        return shown.stdout.decode(errors="replace") if not shown.returncode else None

    crossed, problems = crossed_releases(source, target, notes_at)
    for problem in problems:
        report.manual(problem)

    print(f"upgrade-template: {repository} {source} -> {target}"
          + (" (--check: nothing changed)" if check else ""))
    print(f"clone: {clone.relative_to(root)}")
    for title, key in (("Applied", "applied"), ("Skipped", "skipped"), ("Refused (conflicts)", "refused"),
                       ("Review (left to the project; never conflicts)", "review"), ("Manual", "manual")):
        print(f"\n{title}: {len(report.lists[key])}")
        for item in report.lists[key]:
            line, diff = item if key == "review" else (item, "")
            print(f"  {line}")
            print("".join(f"    {text}\n" for text in diff.splitlines()), end="")
    print("\nReleases crossed:")
    for tag, steps_text in crossed:
        if steps_text is None:
            print(f"  {tag}: command only")
        else:
            print(f"  {tag}: manual steps remain:")
            print("".join(f"    {line}\n" if line else "\n" for line in steps_text.splitlines()), end="")
    refused = report.lists["refused"]
    light = not refused and not report.lists["manual"] and crossed and all(s is None for _, s in crossed)
    print(f"\nLight path: {'yes' if light else 'no'}")
    if refused:
        print(f"{followed['key']} stays {source}: resolve each conflict above, then run the command again,"
              " with --resolved PATH for each file resolved by hand.")
        return 1
    print(f"{followed['key']}: {source} -> {target}" + (" (planned)" if check else ""))
    return 0


try:
    sys.exit(main(sys.argv[1:]))
except Failure as failure:
    print(f"upgrade-template: {failure}", file=sys.stderr)
    sys.exit(2)
PY
