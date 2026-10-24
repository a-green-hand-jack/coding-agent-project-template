"""migrate-assets.sh and new-agent-prompt.sh against fixture repositories: the
project's migrate-project.rules with exact names and wildcards, its validation,
and the handoff prompt's rule about where a session keeps its own files. They
write only to temporary directories."""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
MIGRATE = REPOSITORY / ".agents/scripts/migrate-assets.sh"
PROMPT = REPOSITORY / ".agents/scripts/new-agent-prompt.sh"


class MigrateRules(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="migrate-test-"))
        self.addCleanup(shutil.rmtree, self.temp, ignore_errors=True)
        self.worktree = self.temp / "worktree"
        self.destination = self.temp / "dev"
        (self.worktree / ".agents/scripts").mkdir(parents=True)
        (self.worktree / ".project/state").mkdir(parents=True)
        (self.worktree / ".project/state/initial-prompt.md").write_text("prompt\n")
        (self.destination / ".project").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(self.worktree)], check=True)

    def project_file(self, name: str, text: str = "content\n") -> None:
        (self.worktree / ".project" / name).write_text(text)

    def rules(self, text: str) -> None:
        (self.worktree / ".agents/scripts/migrate-project.rules").write_text(text)

    def migrate(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(MIGRATE), "--to", str(self.destination), *extra],
            cwd=self.worktree, text=True, capture_output=True,
        )

    def copied(self) -> Path:
        (migration,) = (self.destination / ".project/migrations").iterdir()
        return migration

    def test_wildcard_copies_matching_files(self) -> None:
        self.project_file("plan-12.md", "plan\n")
        self.project_file("plan-12-pr1.md", "plan pr1\n")
        self.rules("plan-*.md|copy|\n")
        result = self.migrate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("rule plan-*.md", result.stdout)
        self.assertIn("verified: 3 item(s) identical", result.stdout)
        migration = self.copied()
        self.assertEqual((migration / "plan-12.md").read_text(), "plan\n")
        self.assertEqual((migration / "plan-12-pr1.md").read_text(), "plan pr1\n")

    def test_file_without_a_rule_still_stops(self) -> None:
        self.project_file("plan-12.md")
        self.project_file("msg-coord-pr7.txt")
        self.rules("plan-*.md|copy|\n")
        result = self.migrate()
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertRegex(result.stdout, r"msg-coord-pr7\.txt\s+unknown")
        self.assertIn("migration stopped before copying anything", result.stderr)
        self.assertFalse((self.destination / ".project/migrations").exists())

    def test_without_a_rules_file_a_root_file_stops(self) -> None:
        self.project_file("plan-12.md")
        self.assertEqual(self.migrate().returncode, 3)

    def test_exact_name_wins_over_wildcard(self) -> None:
        self.project_file("plan-12.md")
        self.project_file("plan-13.md")
        # The wildcard comes first in the file, the exact name still decides.
        self.rules("plan-*.md|copy|\nplan-12.md|drop|scratch plan, kept in the Issue\n")
        result = self.migrate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"plan-12\.md\s+drop\s+\S+\s+scratch plan, kept in the Issue")
        self.assertRegex(result.stdout, r"plan-13\.md\s+copy\s+\S+\s+rule plan-\*\.md")
        self.assertEqual([p.name for p in self.copied().glob("plan-*")], ["plan-13.md"])

    def test_first_matching_wildcard_wins(self) -> None:
        self.project_file("plan-12.md")
        self.rules("plan-*|drop|temporary notes\n*.md|copy|\n")
        result = self.migrate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"plan-12\.md\s+drop\s+\S+\s+rule plan-\*: temporary notes")
        self.assertFalse((self.copied() / "plan-12.md").exists())

    def test_wildcard_does_not_match_other_names(self) -> None:
        self.project_file("notes.md")
        self.rules("plan-*.md|copy|\n")
        self.assertEqual(self.migrate().returncode, 3)

    def test_exact_name_rules_behave_as_before(self) -> None:
        self.project_file("setup.log", "log\n")
        self.rules("# comment\n\nsetup.log|copy|\n")
        result = self.migrate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"setup\.log\s+copy\s+\S+\s*\n")
        self.assertNotIn("rule setup.log", result.stdout)
        self.assertEqual((self.copied() / "setup.log").read_text(), "log\n")

    def test_also_and_skip_override_a_single_file(self) -> None:
        self.project_file("plan-12.md")
        self.project_file("msg.txt")
        self.project_file("other.txt")
        self.rules("plan-*.md|copy|\n")
        result = self.migrate("--also", "msg.txt", "--skip", "other.txt=not needed")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"msg\.txt\s+copy\s+\S+\s+copied because --also")
        self.assertRegex(result.stdout, r"other\.txt\s+skip\s+\S+\s+left behind on purpose: not needed")
        # A file a wildcard already migrates cannot be skipped.
        again = self.migrate("--skip", "plan-12.md=no")
        self.assertEqual(again.returncode, 2)

    def assert_rejected(self, rules: str, line: int, message: str) -> None:
        self.rules(rules)
        result = self.migrate()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn(f"migrate-project.rules:{line}:", result.stderr)
        self.assertIn(message, result.stderr)
        self.assertFalse((self.destination / ".project/migrations").exists())

    def test_validation_rejects_slash(self) -> None:
        self.assert_rejected("ok.txt|copy|\nstate/*|copy|\n", 2, "not a plain entry name")

    def test_validation_rejects_login_wildcard(self) -> None:
        self.assert_rejected("login-*|login|\n", 1, "wildcard cannot be a login")

    def test_validation_rejects_wildcards_matching_template_entries(self) -> None:
        for pattern, entry in (("st*", "state"), ("*", "state"), ("work?ree.env", "worktree.env"),
                               ("[hc]*", "home"), ("assets.*", "assets.links"), ("cred*", "credentials")):
            with self.subTest(pattern=pattern):
                self.assert_rejected(f"# first\n{pattern}|copy|\n", 2, f"matches {entry}")

    def test_validation_keeps_the_exact_name_checks(self) -> None:
        self.assert_rejected("state|copy|\n", 1, "template already has a rule for state")
        self.assert_rejected("a.txt|copy|\na.txt|copy|\n", 2, "second rule for a.txt")
        self.assert_rejected("plan-*|drop|\n", 1, "drop needs a reason")
        self.assert_rejected("plan-*|keep|\n", 1, "unknown action")

    def test_wildcard_duplicate_is_a_second_rule(self) -> None:
        self.assert_rejected("plan-*|copy|\nplan-*|copy|\n", 2, "second rule for plan-*")


class HandoffPrompt(unittest.TestCase):
    def test_prompt_tells_the_session_where_its_files_go(self) -> None:
        with tempfile.TemporaryDirectory(prefix="prompt-test-") as temp:
            gh = Path(temp) / "gh"
            gh.write_text(
                "#!/usr/bin/env bash\n"
                "echo '{\"number\":7,\"title\":\"A title\",\"body\":\"\",\"url\":\"https://example.test/7\"}'\n"
            )
            gh.chmod(gh.stat().st_mode | stat.S_IXUSR)
            env = {**os.environ, "PATH": f"{temp}:{os.environ['PATH']}"}
            result = subprocess.run(
                ["bash", str(PROMPT), "7"], cwd=REPOSITORY, env=env, text=True, capture_output=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        flat = " ".join(result.stdout.split())
        self.assertIn("plans, PR body drafts and messages to the coordinator", flat)
        self.assertIn(".project/state/", flat)
        self.assertIn("not in the root of .project/", flat)


if __name__ == "__main__":
    unittest.main()
