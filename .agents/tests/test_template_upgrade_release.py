"""Upgrade a project made from an older real release to the release candidate
(this working tree) with the candidate's upgrade-template.sh; the result must
equal a project made from the candidate, except the project's own files."""
from __future__ import annotations

import fnmatch
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
SCRIPT = REPOSITORY / ".agents/scripts/upgrade-template.sh"
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
        self.old = tags[-2]

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
        differing = {path for path in fresh.keys() | after.keys() if fresh.get(path) != after.get(path)}
        self.assertEqual(differing - owned, set(), result.stdout)
        for path in owned:
            self.assertEqual(after.get(path), before.get(path), f"{path} is the project's own and must not change")
        self.assertEqual(after[REGISTRY], fresh[REGISTRY])


if __name__ == "__main__":
    unittest.main()
