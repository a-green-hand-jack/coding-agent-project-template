"""diagnose-environment.sh's branch-model checks while a repository with only
`main` adopts the template, against an offline bare origin and a stand-in `gh`."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[3]
IDENTITY = ["-c", "user.name=Test", "-c", "user.email=test@example.invalid"]
GH = """#!/bin/sh
[ "$1 $2" = "repo view" ] || exit 1
echo '{"visibility":"PRIVATE","nameWithOwner":"owner/project","defaultBranchRef":{"name":"main"}}'
"""
BRANCH_LINES = ("local dev branch", "origin/dev branch", "GitHub default branch: main")


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *IDENTITY, *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


class BranchModelWhileAdoptingTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory(prefix="diagnose-branches-")
        self.addCleanup(directory.cleanup)
        base = Path(directory.name)
        origin = base / "origin.git"
        git("init", "-q", "--bare", "-b", "main", str(origin), cwd=base)
        self.root = base / "project"
        self.root.mkdir()
        git("init", "-q", "-b", "main", cwd=self.root)
        (self.root / "app.py").write_text("print('product')\n", encoding="utf-8")
        git("add", "-A", cwd=self.root)
        git("commit", "-qm", "product", cwd=self.root)
        git("remote", "add", "origin", str(origin), cwd=self.root)
        git("push", "-q", "origin", "main", cwd=self.root)

        # Adopt the template on a branch from main: copy its tracked tree.
        git("switch", "-q", "-c", "feat/adopt-template", cwd=self.root)
        listed = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                                cwd=REPOSITORY, check=True, capture_output=True, text=True).stdout
        for name in filter(None, listed.split("\0")):
            source, destination = REPOSITORY / name, self.root / name
            if source.is_symlink():
                destination.parent.mkdir(parents=True, exist_ok=True)
                os.symlink(os.readlink(source), destination)
            elif source.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
        git("add", "-A", cwd=self.root)
        git("commit", "-qm", "adopt the template", cwd=self.root)

        bin_dir = base / "bin"
        bin_dir.mkdir()
        (bin_dir / "gh").write_text(GH, encoding="utf-8")
        (bin_dir / "gh").chmod(0o755)
        self.env = {key: value for key, value in os.environ.items()
                    if key not in ("CI", "GITHUB_ACTIONS", "AGENTS_PYTHON")}
        self.env["PATH"] = f"{bin_dir}{os.pathsep}{self.env['PATH']}"
        setup = self.run_script("setup-worktree.sh")
        self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)

    def run_script(self, name: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["bash", f".agents/scripts/shared/{name}"], cwd=self.root, env=self.env,
                              capture_output=True, text=True, check=False)

    def test_branch_checks_warn_before_dev_exists(self) -> None:
        result = self.run_script("diagnose-environment.sh")
        self.assertEqual(result.returncode, 0, result.stdout)
        for line in BRANCH_LINES:
            self.assertIn(f"warn {line} (expected while adopting: the maintainer runs"
                          " .agents/scripts/shared/init-branches.sh after the adoption merges)", result.stdout)
        self.assertNotIn("FAIL", result.stdout)

    def test_branch_checks_fail_once_dev_exists_without_origin_dev(self) -> None:
        git("branch", "dev", cwd=self.root)
        result = self.run_script("diagnose-environment.sh")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("ok   dev branch available", result.stdout)
        self.assertIn("FAIL origin/dev branch (run .agents/scripts/shared/init-branches.sh)", result.stdout)
        self.assertIn("FAIL GitHub default branch: main (run .agents/scripts/shared/init-branches.sh)", result.stdout)

    def test_branch_checks_fail_on_main_without_dev(self) -> None:
        git("switch", "-q", "main", cwd=self.root)
        git("merge", "-q", "--ff-only", "feat/adopt-template", cwd=self.root)
        self.env["SKIP_BRANCH_INIT"] = "1"
        self.assertEqual(self.run_script("setup-worktree.sh").returncode, 0)
        result = self.run_script("diagnose-environment.sh")
        self.assertEqual(result.returncode, 1, result.stdout)
        for line in BRANCH_LINES:
            self.assertIn(f"FAIL {line} (run .agents/scripts/shared/init-branches.sh)", result.stdout)

    def test_python_dependencies_are_checked_for_the_selected_interpreter(self) -> None:
        bare = self.root.parent / "bin" / "bare-python"
        bare.write_text(f"#!/bin/sh\nexec {shutil.which('python3', path=self.env['PATH'])} -S \"$@\"\n", encoding="utf-8")
        bare.chmod(0o755)
        self.env["AGENTS_PYTHON"] = str(bare)
        missing = self.run_script("diagnose-environment.sh")
        self.assertEqual(missing.returncode, 1, missing.stdout)
        self.assertIn(f'FAIL {bare} -I -c "import yaml, markdown_it": PyYAML or markdown-it-py is missing', missing.stdout)
        self.assertIn("export AGENTS_PYTHON=<venv>/bin/python", missing.stdout)
        self.env["AGENTS_PYTHON"] = shutil.which("python3", path=self.env["PATH"])
        present = self.run_script("diagnose-environment.sh")
        self.assertIn(f'ok   {self.env["AGENTS_PYTHON"]} -I -c "import yaml, markdown_it"', present.stdout)

    def test_template_backfill_hint_names_no_fixed_repository(self) -> None:
        registry = self.root / ".agents/content-registry.yaml"
        text = registry.read_text(encoding="utf-8")
        registry.write_text(re.sub(r"^template:\n(?:  .*\n)+", "", text, count=1, flags=re.M), encoding="utf-8")
        result = self.run_script("diagnose-environment.sh")
        self.assertIn("has no `template:` block", result.stdout)
        self.assertNotIn("coding-agent-project-template", result.stdout)
        command = next(line.strip() for line in result.stdout.splitlines() if line.strip().startswith("awk "))
        command = command.replace("<TAG>", "v9.9.9").replace("<TEMPLATE_URL>", "https://example.invalid/derived-template")
        subprocess.run(["bash", "-c", command], cwd=self.root, check=True)
        block = re.search(r"^template:\n((?:  .*\n)+)", registry.read_text(encoding="utf-8"), re.M).group(1)
        self.assertEqual(block, "  repository: https://example.invalid/derived-template\n  version: v9.9.9\n")


class ProjectPythonSelectionTests(unittest.TestCase):
    """The inherited commands run with AGENTS_PYTHON when it is set, otherwise
    with a virtual environment at .project/venv, otherwise with python3 on PATH."""

    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory(prefix="project-python-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name) / "project"
        shutil.copytree(REPOSITORY / ".agents/scripts", self.root / ".agents/scripts", symlinks=True)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.env = {key: value for key, value in os.environ.items()
                    if key not in ("CI", "GITHUB_ACTIONS", "AGENTS_PYTHON")}

    def stub(self, relative: str) -> Path:
        """A stand-in interpreter that only says which path ran it."""
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('#!/bin/sh\nprintf "ran %s\\n" "$0"\n', encoding="utf-8")
        path.chmod(0o755)
        return path

    def run_script(self, name: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["bash", f".agents/scripts/shared/{name}"], cwd=self.root, env=self.env,
                              capture_output=True, text=True, check=False)

    def test_project_venv_python_is_used_when_agents_python_is_unset(self) -> None:
        venv = self.stub(".project/venv/bin/python3")
        diagnose = self.run_script("diagnose-environment.sh")
        self.assertIn(f'ok   {venv} -I -c "import yaml, markdown_it"', diagnose.stdout)
        check = self.run_script("check-development.sh")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertIn(f"ran {venv}", check.stdout)

    def test_agents_python_still_wins_over_the_project_venv(self) -> None:
        venv = self.stub(".project/venv/bin/python3")
        chosen = self.stub("bin/chosen-python")
        self.env["AGENTS_PYTHON"] = str(chosen)
        diagnose = self.run_script("diagnose-environment.sh")
        self.assertIn(f'ok   {chosen} -I -c "import yaml, markdown_it"', diagnose.stdout)
        self.assertNotIn(f"ok   {venv} ", diagnose.stdout)
        check = self.run_script("check-development.sh")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertIn(f"ran {chosen}", check.stdout)


if __name__ == "__main__":
    unittest.main()
