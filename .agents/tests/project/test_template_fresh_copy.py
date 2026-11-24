"""A repository copied from the template has no template release history.

Its first push must pass: the template's own tests compare releases, and in a
copy they skip instead of failing. The copy is made the way a maintainer makes
one: the tracked tree, a fresh repository, and its own `origin`.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
IDENTITY = ["-c", "user.name=Test", "-c", "user.email=test@example.invalid"]
SKIPPED = "the template's own tests need the template's release history"


class CopiedRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory(prefix="template-copy-")
        self.addCleanup(directory.cleanup)
        self.copy = Path(directory.name) / "project"
        self.copy.mkdir()
        listed = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                                cwd=ROOT, check=True, capture_output=True, text=True).stdout
        for name in filter(None, listed.split("\0")):
            source, destination = ROOT / name, self.copy / name
            if not (source.exists() or source.is_symlink()):
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            if source.is_symlink():
                os.symlink(os.readlink(source), destination)
            else:
                shutil.copy2(source, destination)
        for command in (["git", "init", "-q", "-b", "dev"],
                        ["git", "add", "-A"],
                        ["git", *IDENTITY, "commit", "-qm", "a repository copied from the template"],
                        ["git", "remote", "add", "origin", "https://example.invalid/owner/project.git"]):
            subprocess.run(command, cwd=self.copy, check=True, capture_output=True)

    def run_tests(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                       "PYTHONPATH": str(self.copy / ".agents/tests/project")}
        return subprocess.run([sys.executable, "-m", "unittest", *arguments], cwd=self.copy,
                              env=environment, text=True, capture_output=True, check=False)

    def test_the_release_comparisons_skip_instead_of_failing(self) -> None:
        result = self.run_tests("discover", "-v", "-s", ".agents/tests/project",
                                "-p", "test_template_upgrade_release.py")
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output)
        self.assertIn(SKIPPED, output)
        self.assertIn("skipped=", output)
        self.assertNotIn("FAILED", output)
        self.assertNotIn("the release tags are missing", output)

    def test_the_test_move_history_skips_instead_of_failing(self) -> None:
        result = self.run_tests("-v", "test_template_development.DevelopmentContractTests"
                                ".test_normalized_test_discovery_does_not_shrink")
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output)
        self.assertIn(SKIPPED, output)
        self.assertNotIn("no release tag records the historical migration map", output)
