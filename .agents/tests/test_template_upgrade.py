"""upgrade-template.sh against a fixture template repository with three tags."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/upgrade-template.sh"
IDENTITY = ["-c", "user.name=Test", "-c", "user.email=test@example.invalid"]

REGISTRY = """schema_version: 1
template:
  repository: {repository}
  version: {version}
{comment}writing:
  language: {language}
default_scope: project
{fields}entries:
  - path: shared/
    scope: shared
    note: Shared files.
  - path: notes/
    scope: project
    note: The project's own notes.
  - path: TEMPLATE.md
    scope: template
    note: The template's own record.
  - path: README.md
    scope: shared_with_adaptation
    upgrade: review
    note: Rewritten for the project.
  - path: ci/check.yml
    scope: shared_with_adaptation
    optional: true
    note: Optional hosted CI.
  - path: .agents/**/AGENTS.md
    scope: shared_with_adaptation
    note: Directory rules and indexes, adapted by the project.
{extra}"""
COMMENT = "  # The template block's comment, added in v2.\n"
FIELDS = "entry_fields:\n  optional: true when a project may leave the path out.\n"
EXTRAS = """  # Added in v2
  - path: extras/
    scope: shared
    note: Shared tools.
  - path: ci/extra.yml
    scope: shared
    optional: true
    note: Optional, new in v2.
"""
NOTES = {
    "v1": "## v1\n\nFirst.\n",
    "v2": "## v2\n\nSecond.\n\n### Upgrading a project from v1\n\n1. Move the widget by hand.\n\n",
    "v3": "## v3\n\nThird.\n\n### Upgrading a project from v2\n\n**Command only.** The command completes it.\n\n",
}
SKILL = {
    "v1": "# Skill\n\n1. First step.\n2. Second step.\n",
    "v2": "# Skill\n\n1. First step.\n2. Second step, reworded.\n",
    "v3": "# Skill\n\n1. First step, changed.\n2. Second step, reworded.\n",
}
LOCAL_SECTION = "\n## In this repository\n\n- Step 1 (First step): also run the local check.\n"
INDEX = "# Tools\n\n{rules}\n\n## Index\n\n- `a.sh` — does a.\n"
LOCAL_INDEX_LINE = "- `mine.sh` — the project's own tool.\n"
OWN_README = "# My project\n\nBuild it with make.\n"
OWN_WRITING = "writing:\n  language: 中文\n  issue_sections: 最终目标, 怎么办, 验收\n"


def release(version: str, repository: str) -> dict[str, str]:
    """The template's files at a tag."""
    number = int(version[1:])
    files = {
        ".agents/content-registry.yaml": REGISTRY.format(
            repository=repository, version=version, comment=COMMENT if number >= 2 else "",
            language="English" if number < 3 else "Deutsch", fields=FIELDS if number >= 3 else "",
            extra=EXTRAS if number >= 2 else ""),
        "RELEASE_NOTES.md": "# Release notes\n\n" + "".join(NOTES[f"v{n}"] for n in range(number, 0, -1)),
        "shared/plain.txt": "one\n" if number == 1 else "two\n",
        "shared/skill.md": SKILL[version],
        "shared/edited.txt": "a\nb\nc\n" if number < 3 else "a\nb\nC\n",
        "TEMPLATE.md": f"template record {version}\n",
        "notes/plan.txt": f"plan {version}\n",
        "shared/overlap.txt": "x\n" if number < 3 else "z\n",
        "assets/README.md": "assets\n" if number < 2 else "assets, revised\n",
        "README.md": "# Template\n\nStart here.\n" if number < 3 else "# Template\n\nStart here, then run init.\n",
        "ci/check.yml": "on: push\n" if number < 3 else "on: pull_request\n",
        ".agents/tools/AGENTS.md": INDEX.format(rules="Rules." if number < 3 else "Rules, revised."),
    }
    if number < 3:
        files["shared/gone.txt"] = "removed in v3\n"
    if number >= 2:
        files["shared/new.txt"] = "new in v2\n"
        files["extras/tool.sh"] = "#!/bin/sh\necho tool\n"
        files["ci/extra.yml"] = "on: schedule\n"
    return files


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def write(root: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        if name.endswith(".sh"):
            path.chmod(0o755)


def snapshot(root: Path) -> dict[str, bytes]:
    return {str(path.relative_to(root)): path.read_bytes() for path in sorted(root.rglob("*"))
            if path.is_file() and not path.relative_to(root).parts[0] in (".git", ".project")}


class UpgradeTemplateTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory(prefix="upgrade-template-")
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.template = self.base / "template"
        self.template.mkdir()
        git("init", "-q", cwd=self.template)
        for version in ("v1", "v2", "v3"):
            for path in list(self.template.iterdir()):
                if path.name != ".git":
                    shutil.rmtree(path) if path.is_dir() else path.unlink()
            write(self.template, release(version, str(self.template)))
            git("add", "-A", cwd=self.template)
            git(*IDENTITY, "commit", "-qm", version, cwd=self.template)
            git("tag", version, cwd=self.template)

    def project(self, version: str, edited: bool) -> Path:
        """A project made from the template at VERSION: without the scope
        template file and its entry, with its own release notes, README and
        writing conventions, a section in the shared skill, an index line of its
        own in a section-less AGENTS.md, and the optional CI left out; EDITED
        also changes two shared files locally, one of them where the template
        changes it too."""
        root = self.base / f"project-{version}"
        files = release(version, str(self.template))
        del files["TEMPLATE.md"], files["ci/check.yml"]
        files.pop("ci/extra.yml", None)
        registry = files[".agents/content-registry.yaml"]
        registry = registry.replace(
            "  - path: TEMPLATE.md\n    scope: template\n    note: The template's own record.\n", "")
        files[".agents/content-registry.yaml"] = registry.replace(
            registry[registry.index("writing:"):registry.index("default_scope:")], OWN_WRITING)
        files["RELEASE_NOTES.md"] = "# Release notes\n"
        files["shared/skill.md"] += LOCAL_SECTION
        files["README.md"] = OWN_README
        files[".agents/tools/AGENTS.md"] += LOCAL_INDEX_LINE
        if edited:
            files["shared/edited.txt"] = "A\nb\nc\n"
            files["shared/overlap.txt"] = "y\n"
        write(root, files)
        git("init", "-q", cwd=root)
        return root

    def upgrade(self, root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["bash", str(SCRIPT), *arguments], cwd=root, capture_output=True, text=True,
                              check=False)

    def version(self, root: Path) -> str:
        text = (root / ".agents/content-registry.yaml").read_text(encoding="utf-8")
        return text.split("\n  version: ", 1)[1].split("\n", 1)[0]

    def test_check_changes_nothing_and_prints_the_plan(self) -> None:
        root = self.project("v1", edited=True)
        before = snapshot(root)
        result = self.upgrade(root, "--check", "v3")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(snapshot(root), before)
        self.assertFalse((root / ".project/state/template-upgrade/proposals/shared/plain.txt").exists())
        for line in ("shared/plain.txt: replaced",
                     "shared/skill.md: replaced above ## In this repository",
                     "shared/new.txt: added",
                     "extras/tool.sh: added",
                     "shared/gone.txt: removed",
                     "entry extras/ added",
                     "entry ci/extra.yml added",
                     "template block as in v3",
                     "entry_fields added",
                     "TEMPLATE.md: scope template",
                     "notes/plan.txt: project-owned (project)",
                     "ci/check.yml: optional and left out here (a local decision)",
                     "ci/extra.yml: new optional content in v3; adopt it with",
                     "shared/edited.txt: merged with the local text (three-way, no overlap)",
                     "shared/overlap.txt: changed here and in v3; merge proposal with conflict markers:",
                     "Refused (conflicts): 1",
                     "README.md: the project's own (upgrade: review); the release's change:",
                     "    +Start here, then run init.",
                     "assets/README.md: changed in v3; this command never touches it",
                     "shared/skill.md: reconcile its ## In this repository section (step 1",
                     "v3: command only",
                     "v2: manual steps remain:",
                     "1. Move the widget by hand.",
                     "Light path: no",
                     "template.version stays v1"):
            self.assertIn(line, result.stdout)
        self.assertNotIn("writing", result.stdout)

    def test_a_conflict_is_refused_and_the_rest_applied_across_two_releases(self) -> None:
        root = self.project("v1", edited=True)
        result = self.upgrade(root, "v3")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        read = lambda name: (root / name).read_text(encoding="utf-8")
        self.assertEqual(read("shared/plain.txt"), "two\n")
        self.assertEqual(read("shared/skill.md"), SKILL["v3"] + LOCAL_SECTION)
        self.assertEqual(read("shared/edited.txt"), "A\nb\nC\n")
        self.assertEqual(read("shared/overlap.txt"), "y\n")
        self.assertEqual(read("README.md"), OWN_README)
        self.assertEqual(read("shared/new.txt"), "new in v2\n")
        self.assertTrue(os.access(root / "extras/tool.sh", os.X_OK))
        self.assertFalse((root / "shared/gone.txt").exists())
        self.assertFalse((root / "TEMPLATE.md").exists())
        self.assertFalse((root / "ci/check.yml").exists())
        self.assertFalse((root / "ci/extra.yml").exists())
        self.assertEqual(read("notes/plan.txt"), "plan v1\n")
        self.assertEqual(read("assets/README.md"), "assets\n")
        registry = read(".agents/content-registry.yaml")
        self.assertIn("  # Added in v2\n  - path: extras/\n", registry)
        self.assertIn(COMMENT + OWN_WRITING, registry)
        self.assertIn(FIELDS, registry)
        self.assertNotIn("TEMPLATE.md", registry)
        self.assertEqual(self.version(root), "v1")

        proposal = root / ".project/state/template-upgrade/proposals/shared/overlap.txt"
        self.assertEqual(proposal.read_text(encoding="utf-8"), "<<<<<<< here\ny\n=======\nz\n>>>>>>> v3\n")
        shutil.copyfile(proposal, root / "shared/overlap.txt")
        result = self.upgrade(root, "--resolved", "shared/overlap.txt", "v3")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("shared/overlap.txt: --resolved, but conflict markers remain", result.stdout)

        # A resolution by hand that no merge reproduces: still a conflict until --resolved names it.
        (root / "shared/overlap.txt").write_text("y, then z\n", encoding="utf-8")
        result = self.upgrade(root, "v3")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(self.version(root), "v1")
        result = self.upgrade(root, "--resolved", "shared/overlap.txt", "v3")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("shared/overlap.txt: changed here and in v3: resolved here (--resolved)", result.stdout)
        self.assertIn("shared/edited.txt: already has the change of v3", result.stdout)
        self.assertEqual(read("shared/overlap.txt"), "y, then z\n")
        self.assertEqual(self.version(root), "v3")
        self.assertIn(OWN_WRITING, read(".agents/content-registry.yaml"))
        self.assertIn("already v3", self.upgrade(root, "v3").stdout)

    def test_own_documents_and_a_section_less_adaptation_do_not_conflict(self) -> None:
        root = self.project("v1", edited=False)
        result = self.upgrade(root, "v3")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Refused (conflicts): 0", result.stdout)
        self.assertIn("Review (left to the project; never conflicts): 1", result.stdout)
        read = lambda name: (root / name).read_text(encoding="utf-8")
        self.assertEqual(read("README.md"), OWN_README)
        self.assertEqual(read(".agents/tools/AGENTS.md"), INDEX.format(rules="Rules, revised.") + LOCAL_INDEX_LINE)
        self.assertEqual(self.version(root), "v3")

    def test_a_project_without_writing_conventions_gets_none(self) -> None:
        root = self.project("v2", edited=False)
        registry = root / ".agents/content-registry.yaml"
        registry.write_text(registry.read_text(encoding="utf-8").replace(OWN_WRITING, ""), encoding="utf-8")
        result = self.upgrade(root, "v3")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("writing:", registry.read_text(encoding="utf-8"))
        self.assertEqual(self.version(root), "v3")

    def test_a_command_only_release_is_the_light_path_and_runs_offline(self) -> None:
        root = self.project("v2", edited=False)
        (root / "shared/skill.md").write_text(SKILL["v2"], encoding="utf-8")
        self.assertEqual(self.upgrade(root, "--check", "v3").returncode, 0)
        # The clone holds both tags: the repository is no longer needed.
        registry = root / ".agents/content-registry.yaml"
        registry.write_text(registry.read_text(encoding="utf-8").replace(
            str(self.template), str(self.base / "unreachable/template")), encoding="utf-8")
        result = self.upgrade(root, "v3")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Light path: yes", result.stdout)
        self.assertIn("README.md: the project's own (upgrade: review)", result.stdout)
        self.assertEqual((root / "shared/edited.txt").read_text(encoding="utf-8"), "a\nb\nC\n")
        self.assertEqual((root / "shared/skill.md").read_text(encoding="utf-8"), SKILL["v3"])
        self.assertEqual(self.version(root), "v3")

    def test_a_derived_template_moves_only_its_upstream_version(self) -> None:
        root = self.project("v2", edited=False)
        (root / "shared/skill.md").write_text(SKILL["v2"], encoding="utf-8")
        registry = root / ".agents/content-registry.yaml"
        text = registry.read_text(encoding="utf-8")
        own = (f"template:\n  repository: https://example.invalid/derived\n  version: v7\n  upstream:\n"
               f"    repository: {self.template}\n    version: v2\n")
        registry.write_text(text.replace(text[text.index("template:"):text.index(OWN_WRITING)], own),
                            encoding="utf-8")
        result = self.upgrade(root, "v3")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("template.upstream.version: v2 -> v3", result.stdout)
        self.assertIn(own.replace("    version: v2", "    version: v3") + OWN_WRITING,
                      registry.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
