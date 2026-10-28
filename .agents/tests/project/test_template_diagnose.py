"""diagnose-environment.sh's branch-model checks while a repository with only
`main` adopts the template, against an offline bare origin and a stand-in `gh`."""
from __future__ import annotations

import os
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
        self.env = {key: value for key, value in os.environ.items() if key not in ("CI", "GITHUB_ACTIONS")}
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


if __name__ == "__main__":
    unittest.main()
