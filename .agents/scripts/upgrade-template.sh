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
#   - `optional: true` and left out here: a local decision, kept; a new optional
#     path is left for a manual decision;
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
# upgrade section of each release it crosses (RELEASE_NOTES.md at TARGET_TAG),
# and whether the light path applies. --check prints the same plan and changes
# nothing outside .project/state/template-upgrade/.
# Exit 0: done or planned without conflicts; 1: a conflict; 2: an error.
#
# A repository that does not have this script yet runs the target release's copy:
#   bash <(git -C <clone> show TARGET_TAG:.agents/scripts/upgrade-template.sh) TARGET_TAG
set -euo pipefail
exec python3 -I - "$@" <<'PY'
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

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
    match = re.search(rf"^\s+{name}:\s*(\S+)", "".join(block["body"]), re.M)
    return match.group(1) if match else ""


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
        self.proposals = clone.parent / "proposals"
        self.report = Report()

    def blob(self, sha: str) -> bytes:
        return git("cat-file", "blob", sha, cwd=self.clone, raw=True)

    def local(self, path: str):
        file = self.root / path
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
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        if file.is_symlink() or file.exists():
            file.unlink()
        if mode == "120000":
            os.symlink(data.decode(), file)
        else:
            file.write_bytes(data)
            file.chmod(0o755 if mode == "100755" else 0o644)

    def remove(self, path: str) -> None:
        if self.check:
            return
        file = self.root / path
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
        report, state, scope = self.report, self.local(path), scope_in(entry)
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
            data = self.blob(new_sha)
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
            if self.same(state, old_mode, data):
                self.remove(path)
                return report.applied(f"{path}: removed")
            return self.conflict(path, f"{path}: removed in {self.target}, changed here")
        before, after = self.blob(old_sha), self.blob(new_sha)
        if state is None:
            return self.conflict(path, f"{path}: changed in {self.target}, missing here")
        if self.same(state, new_mode, after):
            return report.applied(f"{path}: already as in {self.target}")
        if self.same(state, old_mode, before):
            self.write(path, new_mode, after)
            return report.applied(f"{path}: replaced")
        try:
            here, base, theirs = (data.decode("utf-8") for data in (state[1], before, after))
        except UnicodeDecodeError:
            return self.conflict(path, f"{path}: changed here (not text)")
        if "120000" in (state[0], new_mode):
            return self.conflict(path, f"{path}: changed here (a link)")
        mine, source, target = parts(here), parts(base), parts(theirs)
        if mine[1] is None:
            merged, clean = self.merge(here, base, theirs)
            if not clean:
                return self.conflict(path, f"{path}: changed here and in {self.target}"
                                           f"{self.propose(path, merged, clean)}")
            if merged == here:
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
            report.applied(f"{path}: already as in {self.target} above {SECTION}")
        else:
            merged, clean = self.merge(mine[0], source[0], target[0])
            if not (clean and merged == mine[0]):
                return self.conflict(path, f"{path}: edited above {SECTION} (check 1)"
                                           f"{self.propose(path, merged + chr(10) + mine[1], clean)}")
            report.applied(f"{path}: already has the change of {self.target} above {SECTION}")
        reasons = reconcile(source, target, mine[1]) if mine[1] != target[1] else []
        if reasons:
            report.manual(f"{path}: reconcile its {SECTION} section ({'; '.join(reasons)}); read"
                          f" git -C {self.clone.relative_to(self.root)} diff {self.source} {self.target} -- {path}")


# --- release notes -------------------------------------------------------------

def crossed_releases(notes: str, source: str, target: str) -> tuple[list[tuple[str, str | None]], list[str]]:
    """Each release after source up to target, newest first, with the manual
    steps of its upgrade section (None when it is marked **Command only.**)."""
    entries = [(entry.split(None, 1)[0] if entry.strip() else "", entry)
               for entry in re.split(r"^## ", notes, flags=re.M)[1:]]
    tags = [tag for tag, _ in entries]
    if target not in tags:
        return [], [f"RELEASE_NOTES.md at {target} has no `## {target}` entry; read the notes by hand"]
    problems = [] if source in tags else [
        f"RELEASE_NOTES.md at {target} has no `## {source}` entry; every older entry is listed"]
    crossed = []
    for tag, entry in entries[tags.index(target):]:
        if tag == source or (tag != target and not re.match(r"v\d", tag)):
            break
        match = re.search(r"^### Upgrading\b.*?\n(.*?)(?=^### |\Z)", entry, re.M | re.S)
        if not match:
            crossed.append((tag, "(no upgrade section: read the whole entry)"))
        elif match.group(1).strip().startswith("**Command only.**"):
            crossed.append((tag, None))
        else:
            crossed.append((tag, match.group(1).strip()))
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
    raw = git("diff", "--raw", "-z", "--no-renames", "--no-abbrev", source, target, cwd=clone).split("\0")
    for meta, path in zip(raw[0::2], raw[1::2]):
        if not meta:
            continue
        old_mode, new_mode, old_sha, new_sha, status = meta[1:].split()
        if path == REGISTRY:
            continue
        if path.startswith(NEVER) or path == ".env":
            report.manual(f"{path}: changed in {target}; this command never touches it, compare it by hand")
            continue
        entry = entry_of(path, registries["before" if status == "D" else "after"])
        upgrade.path(old_mode, new_mode, old_sha, new_sha, status[0], path, entry)

    merged = merge_registry(registries["before"], registries["after"], parse_registry(registry_text),
                            source_registry, report, lambda message: upgrade.conflict(REGISTRY, message))
    if not report.lists["refused"]:
        number = followed_template("".join(merged))["line"]
        merged[number] = re.sub(r"(version:\s*)\S+", lambda m: m.group(1) + target, merged[number], count=1)
    if "".join(merged) != registry_text and not check:
        (root / REGISTRY).write_text("".join(merged), encoding="utf-8")

    notes = git("show", f"{target}:RELEASE_NOTES.md", cwd=clone, check=False)
    crossed, problems = crossed_releases(notes.stdout.decode(), source, target) if not notes.returncode else (
        [], [f"{target} has no RELEASE_NOTES.md; read its release by hand"])
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
